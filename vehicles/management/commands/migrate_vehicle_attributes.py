from django.core.management.base import BaseCommand
from django.utils.text import slugify
from vehicles.models import Vehicle, Color, BodyType, FuelType, Gearbox
from vehicles.models_attributes import VehicleAttribute, VehicleAttributeOption

class Command(BaseCommand):
    help = 'Migrates Color, BodyType, FuelType, and Gearbox to VehicleAttribute and specifications JSON'

    def handle(self, *args, **options):
        self.stdout.write("Starting migration of core attributes...")

        # 1. Setup Attributes
        attributes_map = {
            'color': {'name': 'Color', 'model': Color, 'field': 'color'},
            'body_type': {'name': 'Body Type', 'model': BodyType, 'field': 'body_type'},
            'fuel_type': {'name': 'Fuel Type', 'model': FuelType, 'field': 'fuel_type'},
            'gearbox': {'name': 'Gearbox', 'model': Gearbox, 'field': 'gearbox'},
        }

        for key, config in attributes_map.items():
            self.stdout.write(f"Processing attribute: {config['name']} ({key})")
            
            # Create/Get Attribute
            attr, created = VehicleAttribute.objects.get_or_create(
                slug=key,
                defaults={
                    'name': config['name'],
                    'attribute_type': 'select',
                    'is_required': True # Assuming these core fields should be required
                }
            )
            if created:
                self.stdout.write(f"  Created attribute: {attr.name}")

            # Migrate Options
            source_model = config['model']
            field_name = config['field']
            
            for item in source_model.objects.all():
                original_value = getattr(item, field_name)
                slug_value = slugify(original_value)
                
                # Check if option exists
                opt, opt_created = VehicleAttributeOption.objects.get_or_create(
                    attribute=attr,
                    value=slug_value,
                    defaults={'label': original_value}
                )
                if opt_created:
                    self.stdout.write(f"  Created option: {original_value} -> {slug_value}")

        # 2. Migrate Vehicle Data
        self.stdout.write("Migrating Vehicle data...")
        vehicles = Vehicle.objects.all()
        count = 0
        
        for vehicle in vehicles:
            updated = False
            specs = vehicle.specifications or {}
            
            # Color
            if vehicle.color:
                specs['color'] = slugify(vehicle.color.color)
                updated = True
                
            # Body Type
            if vehicle.body_type:
                specs['body_type'] = slugify(vehicle.body_type.body_type)
                updated = True
                
            # Fuel Type
            if vehicle.fuel_type:
                specs['fuel_type'] = slugify(vehicle.fuel_type.fuel_type)
                updated = True
                
            # Gearbox
            if vehicle.gearbox:
                specs['gearbox'] = slugify(vehicle.gearbox.gearbox)
                updated = True
            
            if updated:
                vehicle.specifications = specs
                vehicle.save()
                count += 1
                
        self.stdout.write(self.style.SUCCESS(f"Successfully migrated attributes for {count} vehicles."))
