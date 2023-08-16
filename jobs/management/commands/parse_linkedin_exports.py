import csv
import datetime
import json
import os.path

from dateutil.tz import tz
from django.core.management import BaseCommand

from jobs.models import Job, ETLFile, create_pst_time, List, Item

JOB_ID_KEY = 'jobId'
JOB_TITLE_KEY = 'jobTitle'
COMPANY_NAME_KEY = 'companyName'
POST_DATE_KEY = 'postDate'
LOCATION_KEY = 'location'
JOB_URL_KEY = 'jobUrl'
APPLIED_TO_JOB_KEY = 'applied'
IS_EASY_APPLY_KEY = 'isEasyApply'

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
        update_to_existing_pending_postings = {}
        update_to_existing_applied_posting = {}
        aha_or_canonical_job_posting_encountered = {}
        current_date = datetime.datetime.now()
        today_date = create_pst_time(year=current_date.year, month=current_date.month, day=current_date.day)
        etl_updated_list, new = List.objects.all().get_or_create(name='ETL_updated', user_id=1)
        applied_list, new = List.objects.all().get_or_create(name='Applied', user_id=1)
        archived_list, new = List.objects.all().get_or_create(name='Archived', user_id=1)
        number_of_new_jobs = {}
        new_ids = []
        for linkedin_export_obj in ETLFile.objects.all():
            if os.path.exists(linkedin_export_obj.file_path):
                with open(linkedin_export_obj.file_path, 'r') as linkedin_export:
                    number_of_new_jobs[linkedin_export_obj.file_path] = 0
                    new_post_with_oldest_posted_date[linkedin_export_obj.file_path] = today_date
                    update_to_existing_pending_postings[linkedin_export_obj.file_path] = 0
                    update_to_existing_applied_posting[linkedin_export_obj.file_path] = 0
                    aha_or_canonical_job_posting_encountered[linkedin_export_obj.file_path] = 0
                    print(f"parsing {linkedin_export_obj.file_path}")
                    csvFile = [line for line in csv.reader(linkedin_export)]
                    index = 1
                    csv_mapping = MAPPING.copy()
                    for idx, column in enumerate(csvFile[0]):
                        csv_mapping[column] = idx
                    csvFile = csvFile[1:]
                    for line in csvFile:
                        if line[csv_mapping[COMPANY_NAME_KEY]] not in ["Canonical", 'Aha!']:
                            job = Job.objects.all().filter(
                                linkedin_id=int(line[csv_mapping[JOB_ID_KEY]]),
                                job_title=line[csv_mapping[JOB_TITLE_KEY]],
                                linkedin_link=line[csv_mapping[JOB_URL_KEY]]
                            ).first()
                            new_job = job is None
                            if new_job:
                                print(f"\rparsing new job at line {index}/{len(csvFile)} with {number_of_new_jobs[linkedin_export_obj.file_path]} new jobs so far                        ", end='')
                                number_of_new_jobs[linkedin_export_obj.file_path]+=1
                                job = Job(linkedin_id=int(line[csv_mapping[JOB_ID_KEY]]),
                                          job_title=line[csv_mapping[JOB_TITLE_KEY]],
                                          linkedin_link=line[csv_mapping[JOB_URL_KEY]])
                            else:
                                if job.id not in new_ids:  # needed to distinguish new jobs that were created in
                                    # previous iteration of this loop
                                    if job.item_set.all().filter(list__name='Applied').first() is not None:
                                        Item.objects.all().get_or_create(job=job, list=etl_updated_list)
                                        update_to_existing_applied_posting[linkedin_export_obj.file_path] += 1
                                    else:
                                        update_to_existing_pending_postings[linkedin_export_obj.file_path] += 1
                                    print(f"\rparsing existing job at line {index}/{len(csvFile)} with {number_of_new_jobs[linkedin_export_obj.file_path]} new jobs so far                        ", end='')
                            job.organisation_name = line[csv_mapping[COMPANY_NAME_KEY]]
                            job.location = line[csv_mapping[LOCATION_KEY]]
                            job.remote_work_allowed = False if 'remote' not in job.job_title.lower() else True
                            job.date_posted = datetime.datetime.fromtimestamp(float(line[csv_mapping[POST_DATE_KEY]])).astimezone(tz.gettz('Canada/Pacific'))
                            job.easy_apply = True if line[csv_mapping[IS_EASY_APPLY_KEY]] == 'true' else False
                            job.linkedin_link = line[csv_mapping[JOB_URL_KEY]]
                            applied = line[csv_mapping[APPLIED_TO_JOB_KEY]]== 'True'
                            easy_apply = line[csv_mapping[IS_EASY_APPLY_KEY]]
                            easy_apply = easy_apply if easy_apply != "" else False
                            job.easy_apply = easy_apply
                            job.save()
                            if applied:
                                if job.item_set.all().filter(list__name="Applied").first() is None:
                                    Item.objects.all().get_or_create(job=job, list=applied_list)
                                if job.item_set.all().filter(list__name="Archived").first() is None:
                                    Item.objects.all().get_or_create(job=job, list=archived_list)
                                if job.item_set.all().filter(list__name="ETL_updated").first() is not None:
                                    job.item_set.all().filter(list__name="ETL_updated").delete()
                            if new_job and job.date_posted is not None:
                                if new_post_with_oldest_posted_date[linkedin_export_obj.file_path] > job.date_posted:
                                    new_post_with_oldest_posted_date[linkedin_export_obj.file_path] = job.date_posted
                            new_ids.append(job.id)
                        else:
                            aha_or_canonical_job_posting_encountered[linkedin_export_obj.file_path] += 1
                        index += 1

                print(f"\nparsed {linkedin_export_obj.file_path}")
            linkedin_export_obj.delete()
        print(f"new_post_with_oldest_posted_date=")
        print(json.dumps(new_post_with_oldest_posted_date, indent=4, default=str))
        print(f"number_of_new_jobs=")
        print(json.dumps(number_of_new_jobs, indent=4))
        print(f"aha_or_canonical_job_posting_encountered=")
        print(json.dumps(aha_or_canonical_job_posting_encountered, indent=4))
        print(f"update_to_existing_applied_posting=")
        print(json.dumps(update_to_existing_applied_posting, indent=4))
        print(f"update_to_existing_pending_postings=")
        print(json.dumps(update_to_existing_pending_postings, indent=4))