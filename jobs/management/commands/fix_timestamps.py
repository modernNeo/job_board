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
        updated_times = {
            line[0]: line[1]
            for line in csvFile[1:]
        }
        job_locations = JobLocation.objects.all().exclude(job_board='Indeed')
        number_of_jobs = len(job_locations)
        for index, job_location in enumerate(job_locations):
            job_location.joblocationdateposted_set.all().delete()
            if job_location.id in updated_times:
                JobLocationDatePosted(
                    job_location_posting=job_location,
                    date_posted=pstdatetime.from_epoch(int(updated_times[job_location.id]))
                ).save()
                print(f"processed job {job_location.id} {index}/{number_of_jobs}")
            elif job_location.date_posted is not None:
                JobLocationDatePosted(
                    job_location_posting=job_location,
                    date_posted=job_location.date_posted
                ).save()
                print(f"processed job {job_location.id} {index}/{number_of_jobs}")
            else:
                print(f"skipping job {job_location.id} {index}/{number_of_jobs}")


