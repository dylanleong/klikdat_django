from django.db import models

class IpAsn(models.Model):
    start_ip = models.GenericIPAddressField()
    end_ip = models.GenericIPAddressField()
    asn = models.BigIntegerField()
    country_code = models.CharField(max_length=2)
    organization = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.start_ip} - {self.end_ip}: {self.organization} ({self.country_code})"
