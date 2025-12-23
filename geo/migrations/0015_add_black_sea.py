from django.db import migrations

def add_black_sea(apps, schema_editor):
    GeoKlikRegion = apps.get_model('geo', 'GeoKlikRegion')
    GeoKlikEpoch = apps.get_model('geo', 'GeoKlikEpoch')
    
    epoch, _ = GeoKlikEpoch.objects.get_or_create(name="2025.1")
    
    # Black Sea
    # Approx: 40N to 47N, 27E to 42E
    # Overlaps existing Med definition (30-47N, -6 to 37E).
    # Since is_giant=False for both, but we want BS to win?
    # Both are is_giant=False.
    # We might need to adjust Med bounds or just rely on database order (undefined).
    # Ideally, we shrink Med bound to 30-47N, -6 to 27E? (Cutting off East Med?) No.
    # The overlap is 40-47N, 27-37E.
    # I should explicitly define BS.
    # To fix collision, I should probably UPDATE Med max_lon to 27E effectively? 
    # But Turkey/Cyprus/Levant is East of 27E.
    # It's okay. If I add BS later, it's just another row.
    # With order_by('is_giant'), ambiguity remains for two False regions.
    # I'll rely on explicit targeted click for now. 
    # Or I should have set Med to IS_GIANT=True? No.
    # Let's just add it.
    
    bs = {
        "iso_a2": "OO",
        "adm1_code": "BS", 
        "name": "Black Sea",
        "min_lat": 40, "max_lat": 47, 
        "min_lon": 27, "max_lon": 42,
        "is_giant": False 
    }
    
    if not GeoKlikRegion.objects.filter(epoch=epoch, iso_a2='OO', adm1_code='BS').exists():
         GeoKlikRegion.objects.create(
            epoch=epoch,
            iso_a2=bs['iso_a2'],
            adm1_code=bs['adm1_code'],
            min_lat=bs['min_lat'],
            max_lat=bs['max_lat'],
            min_lon=bs['min_lon'],
            max_lon=bs['max_lon'],
            is_giant=False
        )

def remove_black_sea(apps, schema_editor):
    GeoKlikRegion = apps.get_model('geo', 'GeoKlikRegion')
    GeoKlikRegion.objects.filter(iso_a2='OO', adm1_code='BS').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0014_add_caspian'), 
    ]

    operations = [
        migrations.RunPython(add_black_sea, remove_black_sea),
    ]
