import csv

from django.core.management import BaseCommand

from jobs.models import Job, ETLFile

JOB_ID_INDEX = 0
JOB_TITLE_INDEX = 1
ORGANIZATION_ID_INDEX = 2
ORGANIZATION_NAME_INDEX = 3
LOCATION_INDEX = 8
REMOTE_WORK_ALLOWED_INDEX = 9
WORKPLACE_TYPE_INDEX = 11
DATE_POSTED_INDEX = 16
SOURCE_DOMAIN_INDEX = 19
EASY_APPLY_INDEX = 20
LINKEDIN_LINK_INDEX = 23


class Command(BaseCommand):

    def handle(self, *args, **options):
        for linkedin_export_obj in ETLFile.objects.all():
            with open(linkedin_export_obj.file_path, 'r') as linkedin_export:
                print(f"parsing {linkedin_export_obj.file_path}")
                csvFile = [line for line in csv.reader(linkedin_export)][1:]
                index = 1
                for line in csvFile:
                    print(f" parsing line {index}/{len(csvFile)}")
                    if line[JOB_ID_INDEX] != 'LOCKED 🔒. Please Upgrade your account to continue. ':
                        job = Job.objects.all().filter(
                            job_id=int(line[JOB_ID_INDEX]),
                            job_title=line[JOB_TITLE_INDEX],
                            linkedin_link=line[LINKEDIN_LINK_INDEX]
                        ).first()
                        if job is None:
                            job = Job(job_id=int(line[JOB_ID_INDEX]), job_title=line[JOB_TITLE_INDEX],
                                      linkedin_link=line[LINKEDIN_LINK_INDEX])
                        job.organisation_id = line[ORGANIZATION_ID_INDEX]
                        job.organisation_name = line[ORGANIZATION_NAME_INDEX]
                        job.location = line[LOCATION_INDEX]
                        job.remote_work_allowed = False if line[REMOTE_WORK_ALLOWED_INDEX] == "" else True
                        job.workplace_type = line[WORKPLACE_TYPE_INDEX]
                        job.date_posted = line[DATE_POSTED_INDEX]
                        job.source_domain = line[SOURCE_DOMAIN_INDEX]
                        job.easy_apply = True if line[EASY_APPLY_INDEX] == 'YES' else False
                        job.linkedin_link = line[LINKEDIN_LINK_INDEX]
                        job.save()
                    index+=1
            print(f"parsed {linkedin_export_obj.file_path}")
            linkedin_export_obj.delete()
