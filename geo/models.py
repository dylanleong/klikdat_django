from django.contrib.gis.db import models

class IpAsn(models.Model):
    start_ip = models.GenericIPAddressField()
    end_ip = models.GenericIPAddressField()
    asn = models.BigIntegerField()
    country_code = models.CharField(max_length=2)
    organization = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.start_ip} - {self.end_ip}: {self.organization} ({self.country_code})"

class Continent(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=2, unique=True, null=True, blank=True)
    geometry = models.GeometryField(null=True, blank=True)

    def __str__(self):
        return self.name

class WorldBankBoundary(models.Model):
    iso_a2 = models.CharField(max_length=2, null=True, blank=True)
    adm1_code = models.CharField(max_length=50, null=True, blank=True)
    adm1_name = models.CharField(max_length=255, null=True, blank=True)
    adm2_code = models.CharField(max_length=50, null=True, blank=True)
    adm2_name = models.CharField(max_length=255, null=True, blank=True)
    geometry = models.GeometryField(null=True, blank=True)
    level = models.CharField(max_length=50, blank=True)

    def __str__(self):
        if self.level == 'Admin 2':
            return f"{self.adm2_name} ({self.adm2_code})"
        elif self.level == 'Admin 1':
            return f"{self.adm1_name} ({self.adm1_code})"
        return f"{self.iso_a2} ({self.level})"

class CountryInfo(models.Model):
    country_code = models.CharField(max_length=2, unique=True, primary_key=True)
    country_name = models.CharField(max_length=255)
    country_alpha3_code = models.CharField(max_length=3, null=True, blank=True)
    country_numeric_code = models.CharField(max_length=10, null=True, blank=True)
    capital = models.CharField(max_length=255, null=True, blank=True)
    country_demonym = models.CharField(max_length=255, null=True, blank=True)
    total_area = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    population = models.BigIntegerField(null=True, blank=True)
    idd_code = models.CharField(max_length=10, null=True, blank=True)
    currency_code = models.CharField(max_length=3, null=True, blank=True)
    currency_name = models.CharField(max_length=255, null=True, blank=True)
    currency_symbol = models.CharField(max_length=50, null=True, blank=True)
    lang_code = models.CharField(max_length=10, null=True, blank=True)
    lang_name = models.CharField(max_length=255, null=True, blank=True)
    cctld = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return f"{self.country_name} ({self.country_code})"

class IsoRegion(models.Model):
    country_code = models.CharField(max_length=2)
    region_code = models.CharField(max_length=10) # e.g., US-CA, or just CA depending on data
    region_name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('country_code', 'region_code', 'region_name')

    def __str__(self):
        return f"{self.country_code} - {self.region_name} ({self.region_code})"

class WorldBankRegionMapping(models.Model):
    wb_adm1_code = models.CharField(max_length=50, unique=True)
    country_code = models.CharField(max_length=2)
    wb_region_code = models.CharField(max_length=10)
    wb_region_name = models.CharField(max_length=255)
    iso_region_name = models.CharField(max_length=255, null=True, blank=True)
    iso_region_code = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f"{self.wb_adm1_code} -> {self.iso_region_code or 'N/A'}"

class ImportTask(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    command_name = models.CharField(max_length=100)
    parameters = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    logs = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.command_name} ({self.status})"
    
    class Meta:
        ordering = ['-created_at']

class GeoKlikEpoch(models.Model):
    name = models.CharField(max_length=50, unique=True, help_text="e.g. 2025.1")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Epoch {self.name}"

class GeoKlikRegion(models.Model):
    epoch = models.ForeignKey(GeoKlikEpoch, on_delete=models.CASCADE, related_name='regions')
    iso_a2 = models.CharField(max_length=2)
    adm1_code = models.CharField(max_length=50)
    
    # Static Bounding Box for persistence
    min_lat = models.FloatField()
    max_lat = models.FloatField()
    min_lon = models.FloatField()
    max_lon = models.FloatField()
    
    is_giant = models.BooleanField(default=False, help_text="Area > 456,976 km2")
    
    class Meta:
        unique_together = ('epoch', 'adm1_code')

    def __str__(self):
        return f"{self.iso_a2}-{self.adm1_code} ({self.epoch.name})"

