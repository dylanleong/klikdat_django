from django.db import migrations

def add_ocean_regions(apps, schema_editor):
    GeoKlikRegion = apps.get_model('geo', 'GeoKlikRegion')
    GeoKlikEpoch = apps.get_model('geo', 'GeoKlikEpoch')
    
    epoch, _ = GeoKlikEpoch.objects.get_or_create(name="2025.1")
    
    oceans = [
        # Pacific East: -180 to -70
        {
            "iso_a2": "OO",
            "adm1_code": "PE", # Pacific East
            "name": "Pacific Ocean (East)",
            "min_lat": -60, "max_lat": 60, "min_lon": -180, "max_lon": -70,
            "is_giant": True
        },
        # Pacific West: 120 to 180
        {
            "iso_a2": "OO",
            "adm1_code": "PW", # Pacific West
            "name": "Pacific Ocean (West)",
            "min_lat": -60, "max_lat": 60, "min_lon": 120, "max_lon": 180,
            "is_giant": True
        },
        # Atlantic
        {
            "iso_a2": "OO",
            "adm1_code": "AT", 
            "name": "Atlantic Ocean",
            "min_lat": -60, "max_lat": 60, "min_lon": -70, "max_lon": 20,
            "is_giant": True
        },
        # Indian
        {
            "iso_a2": "OO",
            "adm1_code": "IN", 
            "name": "Indian Ocean",
            "min_lat": -60, "max_lat": 30, "min_lon": 20, "max_lon": 120,
            "is_giant": True
        },
        # Arctic
        {
            "iso_a2": "OO",
            "adm1_code": "AA", 
            "name": "Arctic Ocean",
            "min_lat": 60, "max_lat": 90, "min_lon": -180, "max_lon": 180,
            "is_giant": True
        },
        # Southern
        {
            "iso_a2": "OO",
            "adm1_code": "SO", 
            "name": "Southern Ocean",
            "min_lat": -90, "max_lat": -60, "min_lon": -180, "max_lon": 180,
            "is_giant": True
        }
    ]

    for ocean in oceans:
        if not GeoKlikRegion.objects.filter(
            epoch=epoch, iso_a2=ocean['iso_a2'], adm1_code=ocean['adm1_code']
        ).exists():
            GeoKlikRegion.objects.create(
                epoch=epoch,
                iso_a2=ocean['iso_a2'],
                adm1_code=ocean['adm1_code'],
                min_lat=ocean['min_lat'],
                max_lat=ocean['max_lat'],
                min_lon=ocean['min_lon'],
                max_lon=ocean['max_lon'],
                is_giant=ocean['is_giant']
            )

def remove_ocean_regions(apps, schema_editor):
    GeoKlikRegion = apps.get_model('geo', 'GeoKlikRegion')
    GeoKlikRegion.objects.filter(iso_a2='OO').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0011_geoklikepoch_geoklikregion'), 
    ]

    operations = [
        migrations.RunPython(add_ocean_regions, remove_ocean_regions),
    ]
