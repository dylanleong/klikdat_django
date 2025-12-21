from django.core.management.base import BaseCommand
from vehicles.models import Vehicle
from business.models import BusinessProfile

class Command(BaseCommand):
    help = 'Links existing vehicles to the owner\'s default private business profile'

    def handle(self, *args, **options):
        vehicles = Vehicle.objects.filter(business__isnull=True)
        count = 0
        
        for vehicle in vehicles:
            # Find the private business profile for this owner
            business = BusinessProfile.objects.filter(
                owner=vehicle.owner, 
                is_private=True
            ).first()
            
            if business:
                vehicle.business = business
                vehicle.save()
                count += 1
                self.stdout.write(self.style.SUCCESS(f"Linked vehicle {vehicle.id} ({vehicle.make} {vehicle.model}) to business {business.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Could not find private business profile for user {vehicle.owner.username} (Vehicle {vehicle.id})"))

        self.stdout.write(self.style.SUCCESS(f"Successfully linked {count} vehicles to business profiles"))
