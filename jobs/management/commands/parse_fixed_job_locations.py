import csv
import datetime
import os

from dateutil.tz import tz
from django.core.management import BaseCommand

from jobs.models import JobLocation, ETLFile


class Command(BaseCommand):

    def handle(self, *args, **options):
        csv_files = ETLFile.objects.all()
        if len(csv_files) != 1:
            print(f"got an unexpected number of csv files [{len(csv_files)}]")
            return
        csv_file = csv_files[0]
        if os.path.exists(csv_file.file_path):
            with open(csv_file.file_path, 'r') as linkedin_export:
                print(f"parsing {csv_file.file_path}")
                csvFile = [line for line in csv.reader(linkedin_export)]
                number_of_jobs = len(csvFile)-1
                for index, line in enumerate(csvFile[1:]):
                    job_board_id = line[0]
                    job_location = JobLocation.objects.get(id=job_board_id)
                    experience_level = line[1]
                    location = line[2]
                    date_posted = line[3]
                    if experience_level != "":
                        job_location.experience_level = int(experience_level)
                    if location != "":
                        job_location.location = location
                    if f"{date_posted}".isdigit():
                        job_location.date_posted = datetime.datetime.fromtimestamp(
                            int(date_posted) // 1000
                        ).replace(microsecond=int(date_posted) % 1000 * 10).astimezone(
                            tz.gettz('Canada/Pacific')
                        )
                    job_location.save()
                    print(f"parsed job {index}/{number_of_jobs}")
            csv_file.delete()