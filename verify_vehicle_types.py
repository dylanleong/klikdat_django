import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'klikdat_django.settings')
django.setup()

from vehicles.models import VehicleType

def verify_vehicle_types():
    count = VehicleType.objects.count()
    print(f"VehicleType count: {count}")
    for vt in VehicleType.objects.all():
        print(f"- {vt.vehicle_type}")

if __name__ == "__main__":
    verify_vehicle_types()
