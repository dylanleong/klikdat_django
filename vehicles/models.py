from django.db import models
from django.contrib.auth.models import User


class VehicleType(models.Model):
    """Lookup table for vehicle types (Car, Motorcycle, Van, Truck)"""
    vehicle_type = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.vehicle_type
    
    class Meta:
        ordering = ['vehicle_type']


class Make(models.Model):
    """Lookup table for vehicle manufacturers"""
    make = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.make
    
    class Meta:
        ordering = ['make']


class Model(models.Model):
    """Lookup table for vehicle models"""
    model = models.CharField(max_length=100)
    make = models.ForeignKey(Make, on_delete=models.CASCADE, related_name='models')
    
    def __str__(self):
        return f"{self.make.make} {self.model}"
    
    class Meta:
        ordering = ['make__make', 'model']
        unique_together = ['model', 'make']


class Gearbox(models.Model):
    """Lookup table for gearbox types (Automatic, Manual)"""
    gearbox = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.gearbox
    
    class Meta:
        ordering = ['gearbox']
        verbose_name_plural = 'Gearboxes'


class BodyType(models.Model):
    """Lookup table for body types (Sedan, SUV, Hatchback, etc.)"""
    body_type = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.body_type
    
    class Meta:
        ordering = ['body_type']


class Color(models.Model):
    """Lookup table for vehicle colors"""
    color = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.color
    
    class Meta:
        ordering = ['color']


class FuelType(models.Model):
    """Lookup table for fuel types (Petrol, Diesel, Electric, Hybrid)"""
    fuel_type = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.fuel_type
    
    class Meta:
        ordering = ['fuel_type']


class SellerType(models.Model):
    """Lookup table for seller types (Private, Dealer)"""
    seller_type = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.seller_type
    
    class Meta:
        ordering = ['seller_type']


class Vehicle(models.Model):
    """Main model for vehicle listings"""
    # Relationships
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicles')
    vehicle_type = models.ForeignKey(VehicleType, on_delete=models.PROTECT)
    make = models.ForeignKey(Make, on_delete=models.PROTECT)
    model = models.ForeignKey(Model, on_delete=models.PROTECT)
    gearbox = models.ForeignKey(Gearbox, on_delete=models.PROTECT)
    body_type = models.ForeignKey(BodyType, on_delete=models.PROTECT)
    color = models.ForeignKey(Color, on_delete=models.PROTECT)
    fuel_type = models.ForeignKey(FuelType, on_delete=models.PROTECT)
    seller_type = models.ForeignKey(SellerType, on_delete=models.PROTECT)
    
    # Basic information
    price = models.DecimalField(max_digits=10, decimal_places=2)
    year = models.IntegerField()
    mileage = models.IntegerField(help_text="Mileage in kilometers")
    location = models.CharField(max_length=200)
    
    # Physical attributes
    num_doors = models.IntegerField(null=True, blank=True)
    num_seats = models.IntegerField(null=True, blank=True)
    
    # Electric vehicle specific
    battery_range = models.IntegerField(null=True, blank=True, help_text="Range in kilometers")
    charging_time = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Charging time in hours")
    
    # Engine specifications
    engine_size = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Engine size in liters")
    engine_power = models.IntegerField(null=True, blank=True, help_text="Engine power in horsepower")
    acceleration = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="0-100 km/h in seconds")
    fuel_consumption = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Fuel consumption in L/100km")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.year} {self.make.make} {self.model.model}"
    
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
