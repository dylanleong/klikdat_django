import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from geo.models import WorldBankRegionMapping

class Command(BaseCommand):
    help = 'Import World Bank Region Mapping from CSV'

    def handle(self, *args, **options):
        # Path to the CSV file
        data_dir = os.path.join(settings.BASE_DIR, 'data', 'geo')
        csv_file_path = os.path.join(data_dir, 'map_wb_region_code.csv')

        if not os.path.exists(csv_file_path):
            self.stdout.write(self.style.ERROR(f'File not found at {csv_file_path}'))
            return

        self.stdout.write(f'Importing data from {csv_file_path}...')

        count = 0
        with open(csv_file_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                wb_adm1_code = row.get('ADM1CD_c')
                if not wb_adm1_code:
                    continue
                
                WorldBankRegionMapping.objects.update_or_create(
                    wb_adm1_code=wb_adm1_code,
                    defaults={
                        'country_code': row.get('COUNTRY_CODE'),
                        'wb_region_code': row.get('REGION_CODE'),
                        'wb_region_name': row.get('NAM_1'),
                        'iso_region_name': row.get('ISO31662_SUBDIVISION_NAME'),
                        'iso_region_code': row.get('ISO31662_CODE'),
                    }
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully imported {count} region mappings.'))
