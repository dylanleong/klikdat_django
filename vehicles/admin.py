from django.contrib import admin
from .models import (
    VehicleType, Make, Model,
    SellerType, Vehicle, VehicleProfile, VehicleImage
)
from .models_attributes import VehicleAttribute, VehicleAttributeOption
from import_export.admin import ImportExportModelAdmin
from .resources import (
    VehicleAttributeResource, VehicleAttributeOptionResource,
    MakeResource, ModelResource, VehicleTypeResource, SellerTypeResource
)


@admin.register(VehicleType)
class VehicleTypeAdmin(ImportExportModelAdmin):
    list_display = ['id', 'vehicle_type']
    search_fields = ['vehicle_type']
    resource_class = VehicleTypeResource


class VehicleAttributeOptionInline(admin.TabularInline):
    model = VehicleAttributeOption
    extra = 1

class VehicleImageInline(admin.TabularInline):
    model = VehicleImage
    extra = 1

@admin.register(VehicleAttribute)
class VehicleAttributeAdmin(ImportExportModelAdmin):
    list_display = ['name', 'slug', 'attribute_type', 'is_required']
    list_filter = ['attribute_type', 'is_required', 'vehicle_types']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [VehicleAttributeOptionInline]
    filter_horizontal = ['vehicle_types']
    resource_class = VehicleAttributeResource


@admin.register(VehicleAttributeOption)
class VehicleAttributeOptionAdmin(ImportExportModelAdmin):
    list_display = ['attribute', 'label', 'value']
    list_filter = ['attribute']
    search_fields = ['label', 'value', 'attribute__name']
    resource_class = VehicleAttributeOptionResource


@admin.register(Make)
class MakeAdmin(ImportExportModelAdmin):
    list_display = ['id', 'make']
    search_fields = ['make']
    filter_horizontal = ['vehicle_types']
    resource_class = MakeResource


@admin.register(Model)
class ModelAdmin(ImportExportModelAdmin):
    list_display = ['id', 'model', 'make', 'vehicle_type']
    list_filter = ['make', 'vehicle_type']
    search_fields = ['model', 'make__make']
    resource_class = ModelResource



@admin.register(SellerType)
class SellerTypeAdmin(ImportExportModelAdmin):
    list_display = ['id', 'seller_type']
    search_fields = ['seller_type']
    resource_class = SellerTypeResource


@admin.register(VehicleProfile)
class VehicleProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'seller_type', 'display_name']
    list_filter = ['seller_type']
    search_fields = ['user__username', 'display_name']


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'year', 'make', 'model', 'price', 'owner', 'created_at']
    list_filter = ['vehicle_type', 'make', 'seller_type']
    search_fields = ['title', 'description', 'make__make', 'model__model', 'owner__username', 'location']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']
    inlines = [VehicleImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('owner', 'title', 'description', 'vehicle_type', 'make', 'model', 'year', 'price', 'location')
        }),
        ('Specifications', {
            'fields': ('seller_type', 'mileage', 'specifications')
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
        ('Vehicle Attributes', {
            'fields': ('tax_per_year', 'boot_space'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    class Media:
        js = ('vehicles/js/admin_dep_dropdown.js',)
