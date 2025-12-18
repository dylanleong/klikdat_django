import requests
import json
from django.core.management.base import BaseCommand
from geo.models import WorldBankBoundary

from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Import World Bank boundaries from GeoJSON'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update',
            action='store_true',
            help='Force download of the dataset even if it exists locally',
        )

    def handle(self, *args, **options):
        # Specific URLs provided by user
        # Note: URLs contain spaces, which requests should handle, but we'll quote them just in case if needed
        urls = [
            "https://datacatalogfiles.worldbank.org/ddh-published/0038272/5/DR0095369/World Bank Official Boundaries (GeoJSON)/World Bank Official Boundaries - Admin 0_all_layers.geojson",
            "https://datacatalogfiles.worldbank.org/ddh-published/0038272/5/DR0095369/World Bank Official Boundaries (GeoJSON)/World Bank Official Boundaries - Admin 1.geojson",
            "https://datacatalogfiles.worldbank.org/ddh-published/0038272/5/DR0095369/World Bank Official Boundaries (GeoJSON)/World Bank Official Boundaries - Admin 2.geojson"
        ]
        
        import_dir = os.path.join(settings.DATA_IMPORT_ROOT, 'geo')
        os.makedirs(import_dir, exist_ok=True)
        
        for url in urls:
            # Generate a clean filename from the URL, or use a manual mapping
            if "Admin 0" in url:
                filename = "wb_admin0.geojson"
            elif "Admin 1" in url:
                filename = "wb_admin1.geojson"
            elif "Admin 2" in url:
                filename = "wb_admin2.geojson"
            else:
                filename = os.path.basename(url).replace(" ", "_")
                
            file_path = os.path.join(import_dir, filename)

            if options['update'] or not os.path.exists(file_path):
                self.stdout.write(f"Downloading from {url}...")
                try:
                    # Requests handles spaces in URLs automatically in many versions, but explicit encoding is safer
                    # However, these URLs look like they are served from a file system or object store that allows spaces.
                    # We will try 'requests' default behavior first.
                    response = requests.get(url, stream=True)
                    response.raise_for_status()
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=1024):
                             if chunk:
                                 f.write(chunk)
                except requests.exceptions.RequestException as e:
                    self.stdout.write(self.style.ERROR(f'Failed to download {url}: {e}'))
                    continue
            else:
                 self.stdout.write(f"Using cached file at {file_path}")

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                     data = json.load(f)
            except (IOError, json.JSONDecodeError) as e:
                 self.stdout.write(self.style.ERROR(f'Failed to read/decode {file_path}: {e}'))
                 continue
                
            features = data.get('features', [])
            count = 0
            
            for feature in features:
                props = feature.get('properties', {})
                # Adjust keys based on World Bank GeoJSON structure
                name = props.get('NAME') or props.get('name') or props.get('Name') or props.get('Shape_Name')
                iso_code = props.get('ISO_A3') or props.get('iso_a3') or props.get('ISO3')
                
                if not name:
                    continue
                    
                # We could add a 'level' field to the model if we wanted to distinguish Admin0/1/2
                # inferred from filename or URL.
                level = ""
                if "admin0" in filename: level = "Admin 0"
                elif "admin1" in filename: level = "Admin 1"
                elif "admin2" in filename: level = "Admin 2"

                WorldBankBoundary.objects.update_or_create(
                    name=name,
                    defaults={
                        'iso_code': iso_code,
                        'geometry': feature.get('geometry'),
                        'level': level
                    }
                )
                count += 1
                
            self.stdout.write(self.style.SUCCESS(f'Imported {count} boundaries from {url}'))
