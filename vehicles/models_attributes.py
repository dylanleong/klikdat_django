from django.db import models
from django.utils.text import slugify

class VehicleAttribute(models.Model):
    """
    Defines a dynamic attribute for vehicles (e.g. "Berth", "Axle Config").
    This allows the admin to define what attributes exist.
    """
    ATTRIBUTE_TYPES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('select', 'Select (Dropdown)'),
        ('boolean', 'Checkbox'),
    ]

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, help_text="Unique key for this attribute (e.g. 'berth')")
    attribute_type = models.CharField(max_length=20, choices=ATTRIBUTE_TYPES, default='text')
    
    # Validation helpers
    is_required = models.BooleanField(default=False, help_text="Is this attribute mandatory for the associated vehicle types?")
    
    # Which vehicle types does this attribute apply to?
    # We use a string reference to avoid circular imports with vehicles.models
    vehicle_types = models.ManyToManyField('vehicles.VehicleType', related_name='attributes', blank=True)
    
    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_attribute_type_display()})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class VehicleAttributeOption(models.Model):
    """
    Defines valid options for 'select' type attributes (e.g. "4x2", "6x4" for Axle Config).
    """
    attribute = models.ForeignKey(VehicleAttribute, on_delete=models.CASCADE, related_name='options')
    label = models.CharField(max_length=100, help_text="Display label (e.g. '6x4')")
    value = models.CharField(max_length=100, help_text="Stored value (e.g. '6x4')")
    
    class Meta:
        ordering = ['attribute', 'label']
        unique_together = ['attribute', 'value']

    def __str__(self):
        return f"{self.label}"
