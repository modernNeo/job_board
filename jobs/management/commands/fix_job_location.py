import csv
import datetime
import os

from dateutil.tz import tz
from django.conf import settings
from django.core.management import BaseCommand

from jobs.csv_header import MAPPING, LINKED_IN_KEY
from jobs.models import JobLocation, ExperienceLevel, ETLFile
from jobs.setup_logger import Loggers
from jobs.views.linkedin_scraper import get_job_item

logger = Loggers.get_logger()

class Command(BaseCommand):

    def handle(self, *args, **options):
        if settings.PROD_ENVIRONMENT:
            csv_files = ETLFile.objects.all()
            if len(csv_files) != 1:
                print(f"got an unexpected number of csv files [{len(csv_files)}]")
                return
            csv_file = csv_files[0]
            if os.path.exists(csv_file.file_path):
                parse_job_location_fix(csv_file.file_path)
            csv_file.delete()
        else:
            file_path = '/media/jace/jace_docs/2_personal/jobs_site/exports/2023-10-13_03-01-11_PM_easy_apply.csv'
            parse_job_location_fix(file_path)

def parse_job_location_fix(file):
    with open(file, newline='') as f:
        csvFile = csv.reader(f, delimiter=',', quotechar='|')
        csvFileArr = [line for line in csvFile][1:]
        for line in csvFileArr:
            location = JobLocation.objects.get(id=line[0])
            if line[1] == 'True':
                print(1)
            location.easy_apply = line[1] == 'True'
            location.save()
