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
        
        # Truncate table
        WorldBankBoundary.objects.all().delete()
        self.stdout.write(self.style.WARNING("Truncated WorldBankBoundary table."))

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
                geom_data = feature.get('geometry')

                if not geom_data:
                    continue

                # Skip metadata features often found in GeoJSON
                if props.get('name') and ('CRS' in props.get('name') or 'crs' in props.get('name')):
                    continue

                level = ""
                if "admin0" in filename: level = "Admin 0"
                elif "admin1" in filename: level = "Admin 1"
                elif "admin2" in filename: level = "Admin 2"

                iso_a2 = props.get('ISO_A2') or props.get('iso_a2')
                adm1_code = props.get('ADM1CD_c') or props.get('adm1cd_c')
                adm1_name = props.get('NAM_1') or props.get('nam_1')
                adm2_code = props.get('ADM2CD_c') or props.get('adm2cd_c')
                adm2_name = props.get('NAM_2') or props.get('nam_2')
                
                try:
                    from django.contrib.gis.geos import GEOSGeometry
                    # GEOSGeometry can take a GeoJSON string
                    spatial_geom = GEOSGeometry(json.dumps(geom_data))
                    
                    WorldBankBoundary.objects.create(
                        level=level,
                        iso_a2=iso_a2,
                        adm1_code=adm1_code,
                        adm1_name=adm1_name,
                        adm2_code=adm2_code,
                        adm2_name=adm2_name,
                        geometry=spatial_geom,
                    )
                    count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Failed to process geometry for {adm2_name or adm1_name or iso_a2}: {e}'))
                    continue
                
            self.stdout.write(self.style.SUCCESS(f'Imported {count} boundaries from {url}'))
