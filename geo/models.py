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
    name = models.CharField(max_length=255)
    iso_code = models.CharField(max_length=3, null=True, blank=True)
    geometry = models.GeometryField(null=True, blank=True)
    level = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.name} ({self.iso_code})"

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

class GadmBoundary(models.Model):
    name = models.CharField(max_length=255)
    gid = models.CharField(max_length=50, unique=True, null=True, blank=True)
    level = models.IntegerField(default=0)
    parent_gid = models.CharField(max_length=50, null=True, blank=True)
    geometry = models.GeometryField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} (Level {self.level})"
