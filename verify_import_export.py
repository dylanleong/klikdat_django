
import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'klikdat_django.settings')
django.setup()

from vehicles.models import Make, Model, VehicleType
from vehicles.resources import MakeResource, ModelResource

def verify_import_export():
    print("Verifying Import/Export for Make and Model...")
    
    # 1. Setup Data
    car_type, _ = VehicleType.objects.get_or_create(vehicle_type="Car")
    
    make_name = "TestImportExportMake"
    make, _ = Make.objects.get_or_create(make=make_name)
    make.vehicle_types.add(car_type)
    
    model_name = "TestImportExportModel"
    model, _ = Model.objects.get_or_create(model=model_name, make=make, defaults={'vehicle_type': car_type})
    if not model.vehicle_type:
        model.vehicle_type = car_type
        model.save()
        
    print(f"Created/Found Make: {make} (Types: {[t.vehicle_type for t in make.vehicle_types.all()]})")
    print(f"Created/Found Model: {model} (Type: {model.vehicle_type})")
    
    # 2. Test Make Export
    print("\nTesting Make Export...")
    make_resource = MakeResource()
    dataset = make_resource.export(Make.objects.filter(make=make_name))
    csv_data = dataset.csv
    print("Make CSV Output:")
    print(csv_data)
    
    if make_name in csv_data and "Car" in csv_data:
        print("PASS: Make export contains make name and vehicle type.")
    else:
        print("FAIL: Make export missing data.")
    
    # 3. Test Model Export
    print("\nTesting Model Export...")
    model_resource = ModelResource()
    dataset = model_resource.export(Model.objects.filter(model=model_name))
    csv_data = dataset.csv
    print("Model CSV Output:")
    print(csv_data)
    
    if model_name in csv_data and make_name in csv_data and "Car" in csv_data:
        print("PASS: Model export contains model, make, and vehicle type.")
    else:
        print("FAIL: Model export missing data.")

    # Cleanup
    # model.delete()
    # make.delete()
    # print("\nCleanup done.")

if __name__ == '__main__':
    verify_import_export()
