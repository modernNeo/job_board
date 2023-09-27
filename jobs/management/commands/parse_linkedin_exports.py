import csv
import datetime
import os.path
from enum import Enum

from dateutil.tz import tz
from django.core.management import BaseCommand

from jobs.csv_header import MAPPING, JOB_ID_KEY, LOCATION_KEY, JOB_URL_KEY, JOB_TITLE_KEY, \
    COMPANY_NAME_KEY, IS_EASY_APPLY_KEY, POST_DATE_KEY, APPLIED_TO_JOB_KEY, JOB_CLOSED_KEY, EXPERIENCE_LEVEL_KEY
from jobs.models import Job, ETLFile, List, Item, JobLocation, JobLocationDailyStat, DailyStat, \
    ExportRunTime, create_pst_time_from_datetime, ExperienceLevel


class LineType(Enum):
    JOB_POSTING = 1
    EXPORT_RUN_TIME = 2


class Command(BaseCommand):

    def handle(self, *args, **options):
        APPLIED_LIST_NAME = 'Applied'
        ARCHIVED_LIST_NAME = 'Archived'
        JOB_CLOSED_LIST_NAME = 'Job Closed'
        ETL_UPDATED_LIST_NAME = 'ETL_updated'
        TRUE_String = "True"
        applied_list, new = List.objects.all().get_or_create(name=APPLIED_LIST_NAME, user_id=1)
        archived_list, new = List.objects.all().get_or_create(name=ARCHIVED_LIST_NAME, user_id=1)
        job_closed_list, new = List.objects.all().get_or_create(name=JOB_CLOSED_LIST_NAME, user_id=1)

        mode = LineType.JOB_POSTING
        csv_files = ETLFile.objects.all()

        if len(csv_files) != 1:
            print(f"got an unexpected number of csv files [{len(csv_files)}]")
            return
        csv_file = csv_files[0]
        if os.path.exists(csv_file.file_path):
            jobs_updated_so_far = []
            etl_extraction_start_time = datetime.datetime.strptime(
                csv_file.file_path[-43:-21], "%Y-%m-%d_%I-%M-%S_%p"
            )
            daily_stat = DailyStat(
                date_added=create_pst_time_from_datetime(etl_extraction_start_time),
                earliest_date_for_new_job_location=create_pst_time_from_datetime(etl_extraction_start_time),
                number_of_new_jobs=0, number_of_new_job_locations=0, number_of_existing_inbox_jobs_closed=0,
                number_of_new_inbox_jobs_closed=0, number_of_existing_inbox_jobs_applied=0,
                number_of_new_inbox_jobs_applied=0
            )
            daily_stat.save()
            with open(csv_file.file_path, 'r') as linkedin_export:
                print(f"parsing {csv_file.file_path}")
                csvFile = [line for line in csv.reader(linkedin_export)]
                index = 0
                for idx, column in enumerate(csvFile[0]):
                    MAPPING[column] = idx
                for line in csvFile:
                    if line[0] == 'export_type':
                        mode = LineType.EXPORT_RUN_TIME
                    elif line[0] == 'id':
                        mode = LineType.JOB_POSTING
                    elif mode == LineType.EXPORT_RUN_TIME:
                        ExportRunTime(
                            daily_stat=daily_stat, export_type=line[0],
                            run_time_seconds=int(float(line[1]))
                        ).save()
                    elif mode == LineType.JOB_POSTING:
                        job_location = JobLocation.objects.all().filter(
                            linkedin_id=line[MAPPING[JOB_ID_KEY]],
                            location=line[MAPPING[LOCATION_KEY]],
                            linkedin_link=line[MAPPING[JOB_URL_KEY]],
                            job_posting__job_title=line[MAPPING[JOB_TITLE_KEY]],
                            job_posting__company_name=line[MAPPING[COMPANY_NAME_KEY]],
                            experience_level=None if line[MAPPING[EXPERIENCE_LEVEL_KEY]] == "" else ExperienceLevel[line[MAPPING[EXPERIENCE_LEVEL_KEY]]].value
                        ).first()
                        new_job_location = job_location is None
                        existing_job_that_was_unlisted = False
                        if new_job_location:
                            daily_stat.number_of_new_job_locations += 1
                            job = Job.objects.all().filter(
                                job_title=line[MAPPING[JOB_TITLE_KEY]],
                                company_name=line[MAPPING[COMPANY_NAME_KEY]],
                                easy_apply=line[MAPPING[IS_EASY_APPLY_KEY]] == 'True'
                            ).first()
                            if job is None:
                                job = Job(
                                    job_title=line[MAPPING[JOB_TITLE_KEY]],
                                    company_name=line[MAPPING[COMPANY_NAME_KEY]],
                                    easy_apply=line[MAPPING[IS_EASY_APPLY_KEY]] == 'True'
                                )
                                job.save()
                                daily_stat.number_of_new_jobs += 1
                            job_location = JobLocation(
                                job_posting=job,
                                linkedin_id=line[MAPPING[JOB_ID_KEY]],
                                location=line[MAPPING[LOCATION_KEY]],
                                linkedin_link=line[MAPPING[JOB_URL_KEY]],
                                date_posted=datetime.datetime.fromtimestamp(
                                    int(int(line[MAPPING[POST_DATE_KEY]])/1000)
                                ).astimezone(tz.gettz('Canada/Pacific')),
                                experience_level=None if line[MAPPING[EXPERIENCE_LEVEL_KEY]] == "" else ExperienceLevel[line[MAPPING[EXPERIENCE_LEVEL_KEY]]].value
                            )
                            job_location.save()
                            JobLocationDailyStat(
                                daily_stat=daily_stat,
                                job_location=job_location
                            ).save()
                        else:
                            existing_job_that_was_unlisted = len(job_location.job_posting.item_set.all()) == 0
                        job = job_location.job_posting

                        job_marked_as_applied = line[MAPPING[APPLIED_TO_JOB_KEY]] == TRUE_String
                        job_marked_as_closed = line[MAPPING[JOB_CLOSED_KEY]] == TRUE_String
                        if job_marked_as_closed:
                            if job.id not in jobs_updated_so_far:
                                if existing_job_that_was_unlisted:
                                    daily_stat.number_of_existing_inbox_jobs_closed += 1
                                if new_job_location:
                                    daily_stat.number_of_new_inbox_jobs_closed += 1
                            if job.item_set.all().filter(list__name=JOB_CLOSED_LIST_NAME).first() is None:
                                Item.objects.all().get_or_create(job=job, list=job_closed_list)
                        if job_marked_as_applied:
                            if job.id not in jobs_updated_so_far:
                                if existing_job_that_was_unlisted:
                                    daily_stat.number_of_existing_inbox_jobs_applied += 1
                                if new_job_location:
                                    daily_stat.number_of_new_inbox_jobs_applied += 1
                            if job.item_set.all().filter(list__name=APPLIED_LIST_NAME).first() is None:
                                Item.objects.all().get_or_create(job=job, list=applied_list)
                        if job_marked_as_applied or job_marked_as_closed:
                            if job.item_set.all().filter(list__name=ARCHIVED_LIST_NAME).first() is None:
                                Item.objects.all().get_or_create(job=job, list=archived_list)
                            if job.item_set.all().filter(list__name=ETL_UPDATED_LIST_NAME).first() is not None:
                                job.item_set.all().filter(list__name=ETL_UPDATED_LIST_NAME).delete()
                        if new_job_location and job_location.date_posted is not None:
                            if daily_stat.earliest_date_for_new_job_location > job_location.date_posted:
                                daily_stat.earliest_date_for_new_job_location = job_location.date_posted
                        jobs_updated_so_far.append(job.id)
                        index += 1
                        print(
                            f"parsing new job at line {index}/{len(csvFile)} "
                            f"{daily_stat.number_of_new_jobs} new jobs and {daily_stat.number_of_new_job_locations} "
                            f"new job locations so far"
                        )

                print(f"parsed {csv_file.file_path}")
                daily_stat.save()
        csv_file.delete()
