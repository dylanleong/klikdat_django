import gzip
import requests
import shutil
import os
from django.core.management.base import BaseCommand
from geo.models import IpAsn

class Command(BaseCommand):
    help = 'Imports IP to ASN data from iptoasn.com'

    def handle(self, *args, **options):
        url = "https://iptoasn.com/data/ip2asn-v4.tsv.gz"
        filename = "ip2asn-v4.tsv.gz"
        extracted_filename = "ip2asn-v4.tsv"

        self.stdout.write("Downloading database...")
        response = requests.get(url, stream=True)
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        
        self.stdout.write("Extracting database...")
        with gzip.open(filename, 'rb') as f_in:
            with open(extracted_filename, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        self.stdout.write("Importing data... this may take a while.")
        
        # Clear existing data? Or update? Let's clear for now to avoid dupes/complexity
        IpAsn.objects.all().delete()
        
        batch_size = 10000
        batch = []
        count = 0
        
        with open(extracted_filename, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 5:
                    start_ip, end_ip, asn, country_code, organization = parts[:5]
                    try:
                        batch.append(IpAsn(
                            start_ip=start_ip,
                            end_ip=end_ip,
                            asn=int(asn),
                            country_code=country_code,
                            organization=organization
                        ))
                        
                        if len(batch) >= batch_size:
                            IpAsn.objects.bulk_create(batch)
                            count += len(batch)
                            self.stdout.write(f"Imported {count} records...")
                            batch = []
                    except ValueError:
                         continue # Skip bad lines

            if batch:
                IpAsn.objects.bulk_create(batch)
                count += len(batch)
        
        self.stdout.write(self.style.SUCCESS(f'Successfully imported {count} IP ASN records.'))
        
        # Cleanup
        os.remove(filename)
        os.remove(extracted_filename)
