import requests
import zipfile
import io
import csv
from django.core.management.base import BaseCommand
from geo.models import IsoRegion

from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Import ISO 3166-2 Region data from IP2Location'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update',
            action='store_true',
            help='Force download of the dataset even if it exists locally',
        )

    def handle(self, *args, **options):
        url = "https://www.ip2location.com/downloads/ip2location-iso3166-2.zip"
        
        import_dir = os.path.join(settings.DATA_IMPORT_ROOT, 'geo')
        os.makedirs(import_dir, exist_ok=True)
        file_path = os.path.join(import_dir, 'ip2location-iso3166-2.zip')

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

                # Clear existing data? logic varies, let's update_or_create to be safe or delete_all
                # Since it's reference data, delete all might be cleaner if full replace
                self.stdout.write("Clearing existing ISO Region data...")
                IsoRegion.objects.all().delete()
                
                with z.open(csv_filename) as f:
                    text_file = io.TextIOWrapper(f, encoding='utf-8')
                    reader = csv.reader(text_file)
                    
                    self.stdout.write("Importing data...")
                    # Is there a header? Usually IP2Location CSVs don't have headers or we can skip if looks like one
                    # Sample: "country_code","subdivision_name","code"
                    
                    for row in reader:
                        if len(row) < 3:
                            continue
                        
                        # Check header
                        if row[0].lower() == 'country_code':
                            continue
                            
                        country_code = row[0]
                        subdivision_name = row[1]
                        code = row[2]
                        
                        IsoRegion.objects.create(
                            country_code=country_code,
                            region_name=subdivision_name,
                            region_code=code
                        )
                        count += 1
                        
                        if count % 1000 == 0:
                            self.stdout.write(f"Imported {count} records...")

        except zipfile.BadZipFile:
             self.stdout.write(self.style.ERROR('The downloaded file is not a valid ZIP file.'))
             return
            
        self.stdout.write(self.style.SUCCESS(f'Successfully imported {count} ISO Regions.'))
