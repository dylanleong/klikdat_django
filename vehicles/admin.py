from django.contrib import admin
from .models import (
    VehicleType, Make, Model, Gearbox, BodyType,
    Color, FuelType, SellerType, Vehicle
)


@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'vehicle_type']
    search_fields = ['vehicle_type']


@admin.register(Make)
class MakeAdmin(admin.ModelAdmin):
    list_display = ['id', 'make']
    search_fields = ['make']


@admin.register(Model)
class ModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'model', 'make']
    list_filter = ['make']
    search_fields = ['model', 'make__make']


@admin.register(Gearbox)
class GearboxAdmin(admin.ModelAdmin):
    list_display = ['id', 'gearbox']
    search_fields = ['gearbox']


@admin.register(BodyType)
class BodyTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'body_type']
    search_fields = ['body_type']


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ['id', 'color']
    search_fields = ['color']


@admin.register(FuelType)
class FuelTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'fuel_type']
    search_fields = ['fuel_type']


@admin.register(SellerType)
class SellerTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'seller_type']
    search_fields = ['seller_type']


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['id', 'year', 'make', 'model', 'price', 'owner', 'created_at']
    list_filter = ['vehicle_type', 'make', 'fuel_type', 'gearbox', 'seller_type']
    search_fields = ['make__make', 'model__model', 'owner__username', 'location']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('owner', 'vehicle_type', 'make', 'model', 'year', 'price', 'location')
        }),
        ('Specifications', {
            'fields': ('gearbox', 'body_type', 'color', 'fuel_type', 'seller_type', 'mileage')
        }),
        ('Physical Attributes', {
            'fields': ('num_doors', 'num_seats'),
            'classes': ('collapse',)
        }),
        ('Electric Vehicle', {
            'fields': ('battery_range', 'charging_time'),
            'classes': ('collapse',)
        }),
        ('Engine Specifications', {
            'fields': ('engine_size', 'engine_power', 'acceleration', 'fuel_consumption'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
