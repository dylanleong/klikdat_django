from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from business.models import BusinessProfile
from vehicles.models import SellerProfile

class Command(BaseCommand):
    help = 'Migrates data from SellerProfile to BusinessProfile'

    def handle(self, *args, **options):
        # 1. Ensure all users have a default BusinessProfile
        for user in User.objects.all():
            business, created = BusinessProfile.objects.get_or_create(
                owner=user,
                is_private=True,
                defaults={'name': f"Private Profile ({user.username})"}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created default profile for {user.username}"))

        # 2. copy data from SellerProfile to BusinessProfile
        for seller in SellerProfile.objects.all():
            if not seller.user:
                continue
            
            # Find the business profile for this user
            business = BusinessProfile.objects.filter(owner=seller.user, is_private=True).first()
            if not business:
                # Should not happen given step 1
                continue
            
            # Update business name if display_name exists
            if seller.display_name:
                business.name = seller.display_name
            
            # Copy other fields
            business.logo = seller.logo
            business.website = seller.website
            business.about_us = seller.about_us
            business.contact_number = seller.contact_number
            business.phone_number = seller.phone_number
            business.address_line_1 = seller.address_line_1
            business.address_line_2 = seller.address_line_2
            business.city = seller.city
            business.country = seller.country
            business.opening_hours = seller.opening_hours
            business.save()
            
            # Link the seller profile to the business
            seller.business = business
            seller.save()
            
            self.stdout.write(self.style.SUCCESS(f"Migrated data for {seller.user.username}"))

        self.stdout.write(self.style.SUCCESS("Successfully migrated all profiles"))
