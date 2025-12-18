import requests
import zipfile
import io
import csv
from django.core.management.base import BaseCommand
from geo.models import CountryInfo

from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Import Country Information from IP2Location'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update',
            action='store_true',
            help='Force download of the dataset even if it exists locally',
        )

    def handle(self, *args, **options):
        url = "https://www.ip2location.com/download?token=kcCOO7Z4tSi23TwZrUf5iijv7Czaj7uIQ35u74zu1ZGECBqfXqVOb0tWLi9kixVx&file=DB-COUNTRY"
        
        # Setup path
        import_dir = os.path.join(settings.DATA_IMPORT_ROOT, 'geo')
        os.makedirs(import_dir, exist_ok=True)
        file_path = os.path.join(import_dir, 'DB-COUNTRY.zip')
        
        # Check download
        if options['update'] or not os.path.exists(file_path):
            self.stdout.write("Downloading database...")
            try:
                response = requests.get(url)
                response.raise_for_status()
                with open(file_path, 'wb') as f:
                    f.write(response.content)
            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f'Failed to download file: {e}'))
                return
        else:
             self.stdout.write(f"Using cached file at {file_path}")

        count = 0
        
        self.stdout.write("Extracting and processing...")
        try:
            with zipfile.ZipFile(file_path) as z:
                # Find the CSV file
                csv_filename = None
                for name in z.namelist():
                    if name.lower().endswith('.csv'):
                        csv_filename = name
                        break
                
                if not csv_filename:
                     self.stdout.write(self.style.ERROR('No CSV file found in the ZIP archive.'))
                     return

                self.stdout.write("Clearing existing Country Info data...")
                CountryInfo.objects.all().delete()
                
                with z.open(csv_filename) as f:
                    text_file = io.TextIOWrapper(f, encoding='utf-8')
                    reader = csv.reader(text_file)
                    
                    self.stdout.write("Importing data...")
                    
                    # Columns based on inspection:
                    # 0: country_code, 1: country_name, ..., 3: country_alpha3_code, 4: country_numeric_code
                    # 5: capital, 6: country_demonym, 7: total_area, 8: population, 9: idd_code
                    # 10: currency_code, 11: currency_name, 12: currency_symbol, 13: lang_code, 14: lang_name, 15: cctld
                    
                    for i, row in enumerate(reader):
                        # Skip header if present (heuristic check)
                        if i == 0 and row[0].lower() == 'country_code':
                            continue
                            
                        if len(row) < 16:
                            continue
                        
                        try:
                            CountryInfo.objects.create(
                                country_code=row[0],
                                country_name=row[1],
                                country_alpha3_code=row[3],
                                country_numeric_code=row[4],
                                capital=row[5],
                                country_demonym=row[6],
                                total_area=float(row[7]) if row[7] else None,
                                population=int(row[8]) if row[8] else None,
                                idd_code=row[9],
                                currency_code=row[10],
                                currency_name=row[11],
                                currency_symbol=row[12],
                                lang_code=row[13],
                                lang_name=row[14],
                                cctld=row[15]
                            )
                            count += 1
                        except Exception as e:
                             self.stdout.write(self.style.WARNING(f"Skipping row {i}: {e}"))
                             continue
                        
                        if count % 20 == 0:
                            self.stdout.write(f"Imported {count} records...", ending='\r')
                            
        except zipfile.BadZipFile:
             self.stdout.write(self.style.ERROR('The downloaded file is not a valid ZIP file.'))
             return
            
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully imported {count} Country Info records.'))
