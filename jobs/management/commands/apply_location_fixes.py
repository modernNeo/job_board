import csv
import datetime
import os

from dateutil.tz import tz
from django.core.management import BaseCommand

from jobs.models import ETLFile, JobLocation


class Command(BaseCommand):

    def handle(self, *args, **options):

        csv_files = ETLFile.objects.all()
        if len(csv_files) != 1:
            print(f"got an unexpected number of csv files [{len(csv_files)}]")
            return
        csv_file = csv_files[0]
        if os.path.exists(csv_file.file_path):
            with open(csv_file.file_path, 'r') as job_fixes:
                csvFile = [line for line in csv.reader(job_fixes)]
                for line in csvFile[1:]:
                    try:
                        job_location = JobLocation.objects.get(id=line[0])
                        experience_level = line[1]
                        if experience_level != "":
                            job_location.experience_level = experience_level
                        job_location.location = line[2]
                        date_posted = line[3]
                        if f"{date_posted}".isdigit():
                            job_location.date_posted = datetime.datetime.fromtimestamp(
                                    int(date_posted)//1000
                                ).replace(microsecond=int(date_posted) % 1000*10).astimezone(tz.gettz('Canada/Pacific'))
                        job_location.save()
                    except Exception as e:
                        print(e)