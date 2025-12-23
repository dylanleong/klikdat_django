from django.core.management.base import BaseCommand
from geo.models import WorldBankBoundary, GeoKlikEpoch, GeoKlikRegion, WorldBankRegionMapping
from geo.utils import get_region_area
from django.db import transaction

class Command(BaseCommand):
    help = 'Pre-calculate bounding boxes for GeoKlik regions (Persistence Layer)'

    def handle(self, *args, **options):
        # 1. Ensure active Epoch exists
        epoch, created = GeoKlikEpoch.objects.get_or_create(
            name="2025.1",
            defaults={'is_active': True}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created Epoch {epoch.name}"))

        # 2. Get all ADM1 boundaries
        boundaries = WorldBankBoundary.objects.filter(level="Admin 1")
        count = 0
        
        with transaction.atomic():
            for wb in boundaries:
                # Calculate bounding box
                extent = wb.geometry.extent  # (xmin, ymin, xmax, ymax)
                min_lon, min_lat, max_lon, max_lat = extent
                
                # Calculate area
                area = get_region_area(min_lat, max_lat, min_lon, max_lon)
                is_giant = area > 456976
                
                # Create region record
                GeoKlikRegion.objects.update_or_create(
                    epoch=epoch,
                    adm1_code=wb.adm1_code,
                    defaults={
                        'iso_a2': wb.iso_a2,
                        'min_lat': min_lat,
                        'max_lat': max_lat,
                        'min_lon': min_lon,
                        'max_lon': max_lon,
                        'is_giant': is_giant
                    }
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Processed {count} GeoKlik regions for Epoch {epoch.name}"))
