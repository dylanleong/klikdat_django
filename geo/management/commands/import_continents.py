import requests
import zipfile
import io
import csv
from django.core.management.base import BaseCommand
from geo.models import Continent
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Import continents from IP2Location Multilingual CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update',
            action='store_true',
            help='Force download of the dataset even if it exists locally',
        )

    def handle(self, *args, **options):
        url = "https://www.ip2location.com/download?token=kcCOO7Z4tSi23TwZrUf5iijv7Czaj7uIQ35u74zu1ZGECBqfXqVOb0tWLi9kixVx&file=CON-MUL"
        
        import_dir = os.path.join(settings.DATA_IMPORT_ROOT, 'geo')
        os.makedirs(import_dir, exist_ok=True)
        file_path = os.path.join(import_dir, 'continent-multilingual.zip')

        if options['update'] or not os.path.exists(file_path):
            self.stdout.write(f"Downloading from {url}...")
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

                self.stdout.write("Clearing existing Continent data...")
                Continent.objects.all().delete()
                
                seen_continents = set()
                
                with z.open(csv_filename) as f:
                    text_file = io.TextIOWrapper(f, encoding='utf-8')
                    reader = csv.reader(text_file)
                    
                    count = 0
                    for row in reader:
                        # Format: "lang","country_alpha2_code","continent_code","continent"
                        # We only want English (lang="EN")
                        
                        if len(row) < 4:
                            continue
                            
                        # Header check (heuristic) - usually headers have "lang"
                        if row[0].lower() == 'lang':
                            continue
                            
                        # Check for English
                        if row[0].upper() == 'EN':
                            code = row[2]
                            name = row[3]
                            
                            if code not in seen_continents:
                                Continent.objects.create(
                                    name=name,
                                    code=code,
                                    geometry=None # New source has no geometry
                                )
                                seen_continents.add(code)
                                count += 1
                                
            self.stdout.write(self.style.SUCCESS(f'Successfully imported {count} continents'))

        except zipfile.BadZipFile:
             self.stdout.write(self.style.ERROR('The downloaded file is not a valid ZIP file.'))
             return
