import os
import csv
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from vehicles.models import SellerType, VehicleType, Make, Model
from vehicles.models_attributes import VehicleAttribute, VehicleAttributeOption

class Command(BaseCommand):
    help = 'Import vehicle reference data from CSV files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing data before importing',
        )

    def handle(self, *args, **options):
        import_dir = os.path.join(settings.MEDIA_ROOT, 'import', 'vehicles')
        
        if not os.path.exists(import_dir):
            self.stdout.write(self.style.ERROR(f'Import directory not found: {import_dir}'))
            return

        if options['clear']:
            self.stdout.write("Clearing existing data...")
            # Delete in reverse order of dependence
            
            # Since Vehicles reference Models/Makes/Types with ON_DELETE=PROTECT,
            # we must delete Vehicles first to allow clearing reference data.
            # Warning: This deletes user listings!
            # Warning: This deletes user listings and profiles?
            # Actually VehicleProfile links User to SellerType. If we delete SellerType, we must delete Profile.
            # But Profile is OneToOne with User. So we are just removing the profile, not the User.
            from vehicles.models import Vehicle, VehicleProfile
            
            if Vehicle.objects.exists():
                self.stdout.write(self.style.WARNING("Deleting all Vehicle listings..."))
                Vehicle.objects.all().delete()
                
            if VehicleProfile.objects.exists():
                self.stdout.write(self.style.WARNING("Deleting all Vehicle Profiles..."))
                VehicleProfile.objects.all().delete()
                
            VehicleAttributeOption.objects.all().delete()
            VehicleAttribute.objects.all().delete()
            Model.objects.all().delete()
            Make.objects.all().delete()
            VehicleType.objects.all().delete()
            SellerType.objects.all().delete()
            self.stdout.write("Data cleared.")

        # Process files in alphanumeric order
        files = sorted([f for f in os.listdir(import_dir) if f.endswith('.csv')])
        
        for filename in files:
            file_path = os.path.join(import_dir, filename)
            self.stdout.write(f"Processing {filename}...")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                
                # Strip spaces from header keys if any (just in case)
                reader.fieldnames = [name.strip() for name in reader.fieldnames]

                for row in reader:
                    # Strip whitespace from values
                    row = {k: v.strip() if v else '' for k, v in row.items()}
                    
                    try:
                        self.process_row(filename, row)
                        count += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error processing row in {filename}: {row} - {e}"))
                
                self.stdout.write(self.style.SUCCESS(f"Imported {count} records from {filename}"))

    def process_row(self, filename, row):
        if filename.startswith('00_seller_type'):
            SellerType.objects.update_or_create(
                id=row['id'],
                defaults={'seller_type': row['seller_type']}
            )
            
        elif filename.startswith('01_vehicle_type'):
            schema = row.get('schema')
            if schema:
                try:
                    schema = json.loads(schema)
                except json.JSONDecodeError:
                    schema = {}
            else:
                schema = {}
                
            VehicleType.objects.update_or_create(
                id=row['id'],
                defaults={
                    'vehicle_type': row['vehicle_type'],
                    'schema': schema
                }
            )
            
        elif filename.startswith('02_vehicle_make'):
            make_obj, _ = Make.objects.update_or_create(
                id=row['id'],
                defaults={'make': row['make']}
            )
            
            # Handle M2M vehicle_types
            vt_names = [vt.strip() for vt in row.get('vehicle_types', '').split(',') if vt.strip()]
            if vt_names:
                vts = VehicleType.objects.filter(vehicle_type__in=vt_names)
                make_obj.vehicle_types.set(vts)

        elif filename.startswith('03_vehicle_model'):
            # Lookups
            make_name = row['make']
            vt_name = row['vehicle_type']
            
            try:
                make = Make.objects.get(make=make_name)
                vt = VehicleType.objects.get(vehicle_type=vt_name)
                
                Model.objects.update_or_create(
                    id=row['id'],
                    defaults={
                        'model': row['model'],
                        'make': make,
                        'vehicle_type': vt
                    }
                )
            except (Make.DoesNotExist, VehicleType.DoesNotExist) as e:
                 print(f"Skipping model {row['model']}: {e}")

        elif filename.startswith('04_vehicle_attributes'):
             # id,name,slug,attribute_type,is_required,vehicle_types
             is_required = row.get('is_required', '').lower() in ('true', '1', 'yes')
             
             attr, _ = VehicleAttribute.objects.update_or_create(
                 id=row['id'],
                 defaults={
                     'name': row['name'],
                     'slug': row['slug'],
                     'attribute_type': row['attribute_type'],
                     'is_required': is_required
                 }
             )
             
             vt_names = [vt.strip() for vt in row.get('vehicle_types', '').split(',') if vt.strip()]
             if vt_names:
                 vts = VehicleType.objects.filter(vehicle_type__in=vt_names)
                 attr.vehicle_types.set(vts)

        elif filename.startswith('05_vehicle_attributes_options'):
             # attribute,label,value,id
             # attribute column holds the slug
             attr_slug = row['attribute']
             try:
                 attr = VehicleAttribute.objects.get(slug=attr_slug)
                 
                 VehicleAttributeOption.objects.update_or_create(
                     id=row['id'],
                     defaults={
                         'attribute': attr,
                         'label': row['label'],
                         'value': row['value']
                     }
                 )
             except VehicleAttribute.DoesNotExist:
                 print(f"Skipping option {row['label']}: Attribute {attr_slug} not found")
