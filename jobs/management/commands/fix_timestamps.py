import csv
import os

from django.conf import settings
from django.core.management import BaseCommand

from jobs.models import ETLFile, JobLocation, JobLocationDatePosted, pstdatetime


class Command(BaseCommand):

    def handle(self, *args, **options):
        if settings.PROD_ENVIRONMENT:
            csv_files = ETLFile.objects.all()
            if len(csv_files) != 1:
                print(f"got an unexpected number of csv files [{len(csv_files)}]")
                return
            csv_file = csv_files[0]
            if os.path.exists(csv_file.file_path):
                parse_csv_export(csv_file.file_path)
            csv_file.delete()
        else:
            parse_csv_export(settings.EXPORT_FILE)


def parse_csv_export(file_path):
    with open(file_path, 'r') as linkedin_export:
        print(f"parsing {file_path}")
        csvFile = [line for line in csv.reader(linkedin_export)]
        number_of_lines = len(csvFile) - 1
        for index, line in enumerate(csvFile[1:]):
            try:
                job_location = JobLocation.objects.get(id=line[0])
                job_location.joblocationdateposted_set.all().delete()
                JobLocationDatePosted(
                    job_location_posting=job_location,
                    date_posted=pstdatetime.from_epoch(int(line[1]))
                ).save()
                print(f"parsed job {index}/{number_of_lines}")
            except Exception as e:
                print(f"error {e} {line[0]} - {index}/{number_of_lines}")
