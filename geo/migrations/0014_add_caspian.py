from django.db import migrations

def add_caspian(apps, schema_editor):
    GeoKlikRegion = apps.get_model('geo', 'GeoKlikRegion')
    GeoKlikEpoch = apps.get_model('geo', 'GeoKlikEpoch')
    
    epoch, _ = GeoKlikEpoch.objects.get_or_create(name="2025.1")
    
    # Caspian Sea
    # Approx: 36N to 48N, 46E to 55E
    
    caspian = {
        "iso_a2": "OO",
        "adm1_code": "CS", 
        "name": "Caspian Sea",
        "min_lat": 36, "max_lat": 48, 
        "min_lon": 46, "max_lon": 55,
        "is_giant": False 
    }
    
    if not GeoKlikRegion.objects.filter(epoch=epoch, iso_a2='OO', adm1_code='CS').exists():
         GeoKlikRegion.objects.create(
            epoch=epoch,
            iso_a2=caspian['iso_a2'],
            adm1_code=caspian['adm1_code'],
            min_lat=caspian['min_lat'],
            max_lat=caspian['max_lat'],
            min_lon=caspian['min_lon'],
            max_lon=caspian['max_lon'],
            is_giant=False
        )

def remove_caspian(apps, schema_editor):
    GeoKlikRegion = apps.get_model('geo', 'GeoKlikRegion')
    GeoKlikRegion.objects.filter(iso_a2='OO', adm1_code='CS').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0013_add_mediterranean'), 
    ]

    operations = [
        migrations.RunPython(add_caspian, remove_caspian),
    ]
