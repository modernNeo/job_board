import csv

from django.core.management import BaseCommand

from jobs.models import Job, ETLFile

JOB_URL_KEY = 'jobUrl'
JOB_ID_KEY = 'jobId'
COMPANY_NAME_KEY = 'companyName'
JOB_TITLE_KEY = 'jobTitle'
LOGO_URL_KEY = 'logoUrl'
SCRAPED_LOCATION_KEY = 'scrapedLocation'
LOCATION_KEY = 'location'
IS_REMOTE_KEY = 'isRemote'
WORKPLACE_TYPE_KEY = 'workplaceType'
INSIGHTS_KEY = 'insights'
POST_DATE_KEY = 'postDate'
IS_EASY_APPLY_KEY = 'isEasyApply'
IS_PROMOTED_KEY = 'isPromoted'
APPLICANT_COUNT_KEY = 'applicantCount'
URL_KEY = 'url'
QUERY_KEY = 'query'
CATEGORY_KEY = 'category'
TIMESTAMP_KEY = 'timestamp'
MAPPING = {
    JOB_URL_KEY: None,
    JOB_ID_KEY: None,
    COMPANY_NAME_KEY: None,
    JOB_TITLE_KEY: None,
    LOGO_URL_KEY: None,
    SCRAPED_LOCATION_KEY: None,
    LOCATION_KEY: None,
    IS_REMOTE_KEY: None,
    WORKPLACE_TYPE_KEY: None,
    INSIGHTS_KEY: None,
    POST_DATE_KEY: None,
    IS_EASY_APPLY_KEY: None,
    IS_PROMOTED_KEY: None,
    APPLICANT_COUNT_KEY: None,
    URL_KEY: None,
    QUERY_KEY: None,
    CATEGORY_KEY: None,
    TIMESTAMP_KEY: None
}


class Command(BaseCommand):

    def handle(self, *args, **options):
        for linkedin_export_obj in ETLFile.objects.all():
            with open(linkedin_export_obj.file_path, 'r') as linkedin_export:
                print(f"parsing {linkedin_export_obj.file_path}")
                csvFile = [line for line in csv.reader(linkedin_export)]
                index = 1
                csv_mapping = MAPPING.copy()
                for idx, column in enumerate(csvFile[0]):
                    csv_mapping[column] = idx
                csvFile = csvFile[1:]
                for line in csvFile:
                    print(f"parsing line {index}/{len(csvFile)}")
                    job = Job.objects.all().filter(
                        job_id=int(line[csv_mapping[JOB_ID_KEY]]),
                        job_title=line[csv_mapping[JOB_TITLE_KEY]],
                        linkedin_link=line[csv_mapping[URL_KEY]][:-1]
                    ).first()
                    if job is None:
                        print("new job detected")
                        job = Job(job_id=int(line[csv_mapping[JOB_ID_KEY]]),
                                  job_title=line[csv_mapping[JOB_TITLE_KEY]],
                                  linkedin_link=line[csv_mapping[URL_KEY]][:-1])
                    else:
                        print("job already exists")
                    job.organisation_name = line[csv_mapping[COMPANY_NAME_KEY]]
                    job.location = line[csv_mapping[SCRAPED_LOCATION_KEY]]
                    job.remote_work_allowed = False if line[csv_mapping[IS_REMOTE_KEY]] == "" else True
                    job.workplace_type = line[csv_mapping[WORKPLACE_TYPE_KEY]]
                    job.date_posted = line[csv_mapping[POST_DATE_KEY]]
                    job.easy_apply = True if line[csv_mapping[IS_EASY_APPLY_KEY]] == 'true' else False
                    job.linkedin_link = line[csv_mapping[URL_KEY]][:-1]
                    job.save()
                    index += 1
            print(f"parsed {linkedin_export_obj.file_path}")
            linkedin_export_obj.delete()
