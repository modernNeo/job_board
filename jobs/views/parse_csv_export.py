import csv

from jobs.csv_header import MAPPING, JOB_ID_KEY, LOCATION_KEY, JOB_URL_KEY, JOB_TITLE_KEY, COMPANY_NAME_KEY, \
    EXPERIENCE_LEVEL_KEY, JOB_BOARD, IS_EASY_APPLY_KEY, POST_DATE_KEY, APPLIED_TO_JOB_KEY, JOB_CLOSED_KEY
from jobs.models import JobLocation, ExperienceLevel, JobLocationDailyStat, Item, \
    Job, List, JobLocationDatePosted, pstdatetime


def parse_csv_export(file_path, daily_stat):
    TRUE_String = "True"
    jobs_updated_so_far = []
    ETL_UPDATED_LIST_NAME = 'ETL_updated'

    JOB_CLOSED_LIST_NAME = 'Job Closed'
    job_closed_list, new = List.objects.all().get_or_create(name=JOB_CLOSED_LIST_NAME, user_id=1)
    APPLIED_LIST_NAME = 'Applied'
    applied_list, new = List.objects.all().get_or_create(name=APPLIED_LIST_NAME, user_id=1)
    ARCHIVED_LIST_NAME = 'Archived'
    archived_list, new = List.objects.all().get_or_create(name=ARCHIVED_LIST_NAME, user_id=1)
    RESURFACED_IN_CASE_LIST_NAME = 'Resurfaced In Case'
    job_resurfaced_in_case, new = List.objects.all().get_or_create(name=RESURFACED_IN_CASE_LIST_NAME, user_id=1)

    with open(file_path, 'r') as linkedin_export:
        print(f"parsing {file_path}")
        csvFile = [line for line in csv.reader(linkedin_export)]
        index = 0
        for idx, column in enumerate(csvFile[0]):
            MAPPING[column] = idx
        for line in csvFile[1:]:
            job_location_1 = JobLocation.objects.all().filter(
                job_board_id=line[MAPPING[JOB_ID_KEY]],
                location=line[MAPPING[LOCATION_KEY]],
                job_board_link=line[MAPPING[JOB_URL_KEY]],
                experience_level=None if line[MAPPING[EXPERIENCE_LEVEL_KEY]] == "" else ExperienceLevel[line[MAPPING[EXPERIENCE_LEVEL_KEY]]].value,
                job_board=line[MAPPING[JOB_BOARD]],
                easy_apply=line[MAPPING[IS_EASY_APPLY_KEY]] == 'True'
            )
            job_location = job_location_1.filter(
                job_posting__job_title=line[MAPPING[JOB_TITLE_KEY]],
                job_posting__company_name=line[MAPPING[COMPANY_NAME_KEY]],

            ).first()
            new_job_location = job_location is None
            existing_job_that_was_unlisted = False
            if new_job_location:
                daily_stat.number_of_new_job_locations += 1
                job = Job.objects.all().filter(
                    job_title=line[MAPPING[JOB_TITLE_KEY]],
                    company_name=line[MAPPING[COMPANY_NAME_KEY]],
                ).first()
                if job is None:
                    job = Job(
                        job_title=line[MAPPING[JOB_TITLE_KEY]],
                        company_name=line[MAPPING[COMPANY_NAME_KEY]],
                    )
                    job.save()
                    daily_stat.number_of_new_jobs += 1
                job_location = JobLocation(
                    job_posting=job,
                    job_board_id=line[MAPPING[JOB_ID_KEY]],
                    location=line[MAPPING[LOCATION_KEY]],
                    job_board_link=line[MAPPING[JOB_URL_KEY]],
                    date_posted=pst_epoch_datetime(line[MAPPING[POST_DATE_KEY]]),
                    experience_level=None if line[MAPPING[EXPERIENCE_LEVEL_KEY]] == "" else ExperienceLevel[
                        line[MAPPING[EXPERIENCE_LEVEL_KEY]]].value,
                    job_board=line[MAPPING[JOB_BOARD]],
                    easy_apply=line[MAPPING[IS_EASY_APPLY_KEY]] == 'True'
                )
                job_location.save()
                JobLocationDatePosted(
                    date_posted=pstdatetime.from_epoch(int(line[MAPPING[POST_DATE_KEY]])).pst,
                    job_location_posting=job_location
                ).save()
                JobLocationDailyStat(
                    daily_stat=daily_stat,
                    job_location=job_location
                ).save()
            else:
                existing_job_that_was_unlisted = len(job_location.job_posting.item_set.all()) == 0
            job = job_location.job_posting

            job_marked_as_applied = line[MAPPING[APPLIED_TO_JOB_KEY]] != ""
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
                applied_item = job.item_set.all().filter(list__name=APPLIED_LIST_NAME).first()
                pst_date_added = pstdatetime.from_epoch(int(line[MAPPING[APPLIED_TO_JOB_KEY]]))
                if applied_item is None:
                    Item.objects.all().get_or_create(
                        job=job, list=applied_list, date_added=pst_date_added
                    )
                else:
                    applied_item.date_added = pst_date_added
                    applied_item.save()

            # before applying the archived tag to the job location, let's first make sure any existing
            # presence of that tag on this location is accurate, and the only way I have to currently
            # do that is just by placing it back in the inbox
            archived_job_item = job.item_set.all().filter(list__name=ARCHIVED_LIST_NAME).first()
            if archived_job_item is not None:
                job_properly_marked_as_applied = False
                other_list_item_presence_detected = False
                other_job_items = job.item_set.all().exclude(id=archived_job_item.id)
                for other_job_item in other_job_items:
                    if other_job_item.list_name == APPLIED_LIST_NAME:
                        if job_marked_as_applied:
                            job_properly_marked_as_applied = True
                        else:
                            # job might need to be looked at to see why it might not appear in the inbox
                            Item.objects.all().get_or_create(job=job, list=job_resurfaced_in_case)

                    else:
                        # job might need to be looked at to see why it might not appear in the inbox
                        other_list_item_presence_detected = True
                if other_list_item_presence_detected and not job_properly_marked_as_applied:
                    Item.objects.all().get_or_create(job=job, list=job_resurfaced_in_case)

            if job_marked_as_applied or job_marked_as_closed:
                if job.item_set.all().filter(list__name=ARCHIVED_LIST_NAME).first() is None:
                    Item.objects.all().get_or_create(job=job, list=archived_list)
                if job.item_set.all().filter(list__name=ETL_UPDATED_LIST_NAME).first() is not None:
                    job.item_set.all().filter(list__name=ETL_UPDATED_LIST_NAME).delete()
            if new_job_location and job_location.get_latest_posted_date() is not None:
                if daily_stat.earliest_date_for_new_job_location > job_location.get_latest_posted_date():
                    daily_stat.earliest_date_for_new_job_location = job_location.get_latest_posted_date()
            jobs_updated_so_far.append(job.id)
            index += 1
            print(
                f"parsing new job at line {index}/{len(csvFile)} "
                f"{daily_stat.number_of_new_jobs} new jobs and {daily_stat.number_of_new_job_locations} "
                f"new job locations so far"
            )

        print(f"parsed {file_path}")
        daily_stat.save()