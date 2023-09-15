import csv
import datetime
import json
import os.path

from dateutil.tz import tz
from django.core.management import BaseCommand

from jobs.models import Job, ETLFile, create_pst_time, List, Item, JobLocation, JobLocationDailyStat, DailyStat

JOB_ID_KEY = 'jobId'
JOB_TITLE_KEY = 'jobTitle'
COMPANY_NAME_KEY = 'companyName'
POST_DATE_KEY = 'postDate'
LOCATION_KEY = 'location'
JOB_URL_KEY = 'jobUrl'
APPLIED_TO_JOB_KEY = 'applied'
IS_EASY_APPLY_KEY = 'isEasyApply'
JOB_CLOSED_KEY = 'closed'

LOGO_URL_KEY = 'logoUrl'
SCRAPED_LOCATION_KEY = 'scrapedLocation'
IS_REMOTE_KEY = 'isRemote'
WORKPLACE_TYPE_KEY = 'workplaceType'
INSIGHTS_KEY = 'insights'
IS_PROMOTED_KEY = 'isPromoted'
APPLICANT_COUNT_KEY = 'applicantCount'
URL_KEY = 'url'
QUERY_KEY = 'query'
CATEGORY_KEY = 'category'
TIMESTAMP_KEY = 'timestamp'
MAPPING = {
    JOB_ID_KEY: None,
    JOB_TITLE_KEY: None,
    COMPANY_NAME_KEY: None,
    POST_DATE_KEY: None,
    LOCATION_KEY: None,
    JOB_URL_KEY: None,
    APPLIED_TO_JOB_KEY: None,
    IS_EASY_APPLY_KEY: None,
    JOB_CLOSED_KEY : None,

    LOGO_URL_KEY: None,
    SCRAPED_LOCATION_KEY: None,
    IS_REMOTE_KEY: None,
    WORKPLACE_TYPE_KEY: None,
    INSIGHTS_KEY: None,
    IS_PROMOTED_KEY: None,
    APPLICANT_COUNT_KEY: None,
    URL_KEY: None,
    QUERY_KEY: None,
    CATEGORY_KEY: None,
    TIMESTAMP_KEY: None
}


class Command(BaseCommand):

    def handle(self, *args, **options):
        new_post_with_oldest_posted_date = {}
        current_date = datetime.datetime.now()
        today_date = create_pst_time(year=current_date.year, month=current_date.month, day=current_date.day)
        applied_list, new = List.objects.all().get_or_create(name='Applied', user_id=1)
        archived_list, new = List.objects.all().get_or_create(name='Archived', user_id=1)
        job_closed_list, new = List.objects.all().get_or_create(name='Job Closed', user_id=1)
        number_of_new_jobs_per_file = {}
        total_number_of_new_jobs = 0
        total_number_of_new_job_locations = 0
        new_ids = []
        daily_stat = DailyStat()
        earliest_job_location_date_updated = today_date
        daily_stat.save()
        print("first run in debugging to ensure the date_posted check is working on line 88ish")
        for linkedin_export_obj in ETLFile.objects.all():
            if os.path.exists(linkedin_export_obj.file_path):
                with open(linkedin_export_obj.file_path, 'r') as linkedin_export:
                    number_of_new_jobs_per_file[linkedin_export_obj.file_path] = 0
                    new_post_with_oldest_posted_date[linkedin_export_obj.file_path] = today_date
                    print(f"parsing {linkedin_export_obj.file_path}")
                    csvFile = [line for line in csv.reader(linkedin_export)]
                    index = 1
                    csv_mapping = MAPPING.copy()
                    for idx, column in enumerate(csvFile[0]):
                        csv_mapping[column] = idx
                    csvFile = csvFile[1:]
                    for line in csvFile:
                        job_location = JobLocation.objects.all().filter(
                            linkedin_id=line[csv_mapping[JOB_ID_KEY]],
                            location=line[csv_mapping[LOCATION_KEY]],
                            linkedin_link=line[csv_mapping[JOB_URL_KEY]],
                            job_posting__job_title=line[csv_mapping[JOB_TITLE_KEY]],
                            job_posting__organisation_name=line[csv_mapping[COMPANY_NAME_KEY]]
                        ).first()
                        new_job = job_location is None
                        if new_job:
                            print(f"\rparsing new job at line {index}/{len(csvFile)} with {number_of_new_jobs_per_file[linkedin_export_obj.file_path]} new jobs so far                        ", end='')
                            number_of_new_jobs_per_file[linkedin_export_obj.file_path]+=1
                            total_number_of_new_job_locations += 1
                            job = Job.objects.all().filter(
                                job_title=line[csv_mapping[JOB_TITLE_KEY]],
                                organisation_name=line[csv_mapping[COMPANY_NAME_KEY]],
                                easy_apply=line[csv_mapping[IS_EASY_APPLY_KEY]] == 'True'
                            ).first()
                            if job is None:
                                job = Job(
                                    job_title=line[csv_mapping[JOB_TITLE_KEY]],
                                    organisation_name=line[csv_mapping[COMPANY_NAME_KEY]],
                                    easy_apply=line[csv_mapping[IS_EASY_APPLY_KEY]] == 'True'
                                )
                                job.save()
                                total_number_of_new_jobs += 1
                            job_location = JobLocation(
                                job_posting=job,
                                linkedin_id=line[csv_mapping[JOB_ID_KEY]],
                                location=line[csv_mapping[LOCATION_KEY]],
                                linkedin_link=line[csv_mapping[JOB_URL_KEY]],
                                date_posted=datetime.datetime.fromtimestamp(float(line[csv_mapping[POST_DATE_KEY]])).astimezone(tz.gettz('Canada/Pacific')),
                            )
                            job_location.save()
                            JobLocationDailyStat(
                                daily_stat=daily_stat,
                                job_location=job_location
                            ).save()
                        elif job_location.id not in new_ids:  # needed to distinguish new jobs that were created in
                            # previous iteration of this loop
                            job = job_location.job_posting
                            print(f"\rparsing existing job at line {index}/{len(csvFile)} with {number_of_new_jobs_per_file[linkedin_export_obj.file_path]} new jobs so far                        ", end='')


                        if line[csv_mapping[APPLIED_TO_JOB_KEY]] == 'True':
                            if job.item_set.all().filter(list__name="Applied").first() is None:
                                Item.objects.all().get_or_create(job=job, list=applied_list)
                            if job.item_set.all().filter(list__name="Archived").first() is None:
                                Item.objects.all().get_or_create(job=job, list=archived_list)
                            if job.item_set.all().filter(list__name="ETL_updated").first() is not None:
                                job.item_set.all().filter(list__name="ETL_updated").delete()
                        if line[csv_mapping[JOB_CLOSED_KEY]] == 'True':
                            if job.item_set.all().filter(list__name="Job Closed").first() is None:
                                Item.objects.all().get_or_create(job=job, list=job_closed_list)
                            if job.item_set.all().filter(list__name="Archived").first() is None:
                                Item.objects.all().get_or_create(job=job, list=archived_list)
                            if job.item_set.all().filter(list__name="ETL_updated").first() is not None:
                                job.item_set.all().filter(list__name="ETL_updated").delete()
                        if new_job and job_location.date_posted is not None:
                            if earliest_job_location_date_updated > job_location.date_posted:
                                earliest_job_location_date_updated = job_location.date_posted
                            if new_post_with_oldest_posted_date[linkedin_export_obj.file_path] > job_location.date_posted:
                                new_post_with_oldest_posted_date[linkedin_export_obj.file_path] = job_location.date_posted
                        new_ids.append(job.id)
                        index += 1

                print(f"\nparsed {linkedin_export_obj.file_path}")
            linkedin_export_obj.delete()
        print(f"new_post_with_oldest_posted_date=")
        print(json.dumps(new_post_with_oldest_posted_date, indent=4, default=str))
        print(f"number_of_new_jobs=")
        print(json.dumps(number_of_new_jobs_per_file, indent=4))
        daily_stat.number_of_new_jobs=total_number_of_new_jobs
        daily_stat.number_of_new_job_locations=total_number_of_new_job_locations
        daily_stat.earliest_date_for_new_job_location=earliest_job_location_date_updated
        daily_stat.save()