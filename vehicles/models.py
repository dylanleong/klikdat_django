from django.db import models
from django.contrib.auth.models import User


class VehicleType(models.Model):
    """Lookup table for vehicle types (Car, Motorcycle, Van, Truck)"""
    vehicle_type = models.CharField(max_length=50, unique=True)
    schema = models.JSONField(default=dict, blank=True, help_text="JSON schema definition for dynamic attributes")
    
    def __str__(self):
        return self.vehicle_type
    
    class Meta:
        ordering = ['vehicle_type']


class Make(models.Model):
    """Lookup table for vehicle manufacturers"""
    make = models.CharField(max_length=100, unique=True)
    vehicle_types = models.ManyToManyField(VehicleType, related_name='makes')
    
    def __str__(self):
        return self.make
    
    class Meta:
        ordering = ['make']


class Model(models.Model):
    """Lookup table for vehicle models"""
    model = models.CharField(max_length=100)
    make = models.ForeignKey(Make, on_delete=models.CASCADE, related_name='models')
    vehicle_type = models.ForeignKey(VehicleType, on_delete=models.CASCADE, related_name='models', null=True)
    
    def __str__(self):
        return f"{self.make.make} {self.model}"
    
    class Meta:
        ordering = ['make__make', 'model']
        unique_together = ['model', 'make']



# REPLACED: Color, BodyType, FuelType, Gearbox models are removed.
# Their data is now stored in Vehicle.specifications and defined in VehicleAttribute.
# If you need to add choices, use the admin panel for VehicleAttributeOption.


class SellerType(models.Model):
    """Lookup table for seller types (Private, Dealer)"""
    seller_type = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.seller_type
    
    class Meta:
        ordering = ['seller_type']


class VehicleProfile(models.Model):
    """User profile specific to the vehicles module"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    seller_type = models.ForeignKey(SellerType, on_delete=models.PROTECT)
    display_name = models.CharField(max_length=100, blank=True, help_text="Optional display name for listings")
    contact_number = models.CharField(max_length=20, blank=True, help_text="Contact number for vehicle sales")
    
    def __str__(self):
        return f"{self.user.username}'s Vehicle Profile"


class Vehicle(models.Model):
    """Main model for vehicle listings"""
    # Relationships
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicles')
    vehicle_type = models.ForeignKey(VehicleType, on_delete=models.PROTECT)
    make = models.ForeignKey(Make, on_delete=models.PROTECT)
    model = models.ForeignKey(Model, on_delete=models.PROTECT)
    seller_type = models.ForeignKey(SellerType, on_delete=models.PROTECT, null=True, blank=True)
    
    # Basic information
    title = models.CharField(max_length=200, null=True, blank=True, help_text="Short title/headline for the listing")
    description = models.TextField(null=True, blank=True, help_text="Detailed description of the vehicle")
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    mileage = models.IntegerField(help_text="Mileage in kilometers", null=True, blank=True)
    location = models.CharField(max_length=200, null=True, blank=True)
    
    # Dynamic specifications
    specifications = models.JSONField(default=dict, blank=True)
    
    # Physical attributes
    # DEPRECATED: These will be moved to specifications
    num_doors = models.IntegerField(null=True, blank=True)
    num_seats = models.IntegerField(null=True, blank=True)
    
    # Electric vehicle specific
    # DEPRECATED: These will be moved to specifications
    battery_range = models.IntegerField(null=True, blank=True, help_text="Range in kilometers")
    charging_time = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Charging time in hours")
    
    # Engine specifications
    # DEPRECATED: These will be moved to specifications
    engine_size = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Engine size in liters")
    engine_power = models.IntegerField(null=True, blank=True, help_text="Engine power in horsepower")
    acceleration = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="0-100 km/h in seconds")
    fuel_consumption = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Fuel consumption in L/100km")
    
    # Practical details
    tax_per_year = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Annual tax amount")
    boot_space = models.IntegerField(null=True, blank=True, help_text="Boot space in liters")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def clean(self):
        super().clean()
        from django.core.exceptions import ValidationError
        
        # Validate Make/Model consistency
        if self.make_id and self.model_id:
            if self.model.make_id != self.make_id:
                raise ValidationError({
                    'model': f"Model '{self.model.model}' does not belong to make '{self.make.make}'."
                })
        
        # Validate VehicleType consistency
        if self.vehicle_type_id:
            # Check if make supports this vehicle type
            if self.make_id and not self.make.vehicle_types.filter(id=self.vehicle_type_id).exists():
                raise ValidationError({
                    'make': f"Make '{self.make.make}' does not produce vehicles of type '{self.vehicle_type.vehicle_type}'."
                })
                
            # Check if model belongs to this vehicle type
            if self.model_id and self.model.vehicle_type_id:
                if self.model.vehicle_type_id != self.vehicle_type_id:
                    raise ValidationError({
                        'model': f"Model '{self.model.model}' is defined as '{self.model.vehicle_type.vehicle_type}', not '{self.vehicle_type.vehicle_type}'."
                    })
    
    def save(self, *args, **kwargs):
        self.clean() # Optional: Force clean on save, but usually handled by forms
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.year} {self.make} {self.model} - {self.price}"
    
    class Meta:
        ordering = ['-created_at']



class VehicleImage(models.Model):
    """Model for vehicle images"""
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='vehicle_images/')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.vehicle}"
    
    def save(self, *args, **kwargs):
        # If this image is set as primary, unset others
        if self.is_primary:
            VehicleImage.objects.filter(vehicle=self.vehicle, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)


class Favorite(models.Model):
    """Model for user favorite vehicles"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'vehicle']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} likes {self.vehicle}"
