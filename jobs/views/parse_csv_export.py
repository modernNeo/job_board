import csv

from jobs.csv_header import MAPPING, JOB_ID_KEY, LOCATION_KEY, JOB_URL_KEY, JOB_TITLE_KEY, COMPANY_NAME_KEY, \
    EXPERIENCE_LEVEL_KEY, JOB_BOARD, IS_EASY_APPLY_KEY, POST_DATE_KEY, APPLIED_TO_JOB_KEY, JOB_CLOSED_KEY
from jobs.models import JobLocation, ExperienceLevel, JobLocationDailyStat, JobItem, JobLocationDatePostedItem, \
    Job, List, JobLocationDatePosted, pstdatetime

JOB_CLOSED_LIST_NAME = 'Job Closed'
APPLIED_LIST_NAME = 'Applied'
TRUE_String = "True"
ARCHIVED_LIST_NAME = 'Archived'
ETL_UPDATED_LIST_NAME = 'ETL_updated'


def parse_csv_export(file_path, daily_stat):
    jobs_updated_so_far = []
    job_closed_list, new = List.objects.all().get_or_create(name=JOB_CLOSED_LIST_NAME, user_id=1)
    applied_list, new = List.objects.all().get_or_create(name=APPLIED_LIST_NAME, user_id=1)
    archived_list, new = List.objects.all().get_or_create(name=ARCHIVED_LIST_NAME, user_id=1)
    RESURFACED_IN_CASE = 'Resurfaced In Case'
    resurfaced_in_case_list, new = List.objects.all().get_or_create(name=RESURFACED_IN_CASE, user_id=1)
    RESURFACED_APPLIED_OR_CLOSED_INBOX = 'Resurfaced Applied or Closed Job'
    resurfaced_applied_or_closed_list, new = List.objects.all().get_or_create(name=RESURFACED_APPLIED_OR_CLOSED_INBOX, user_id=1)

    with open(file_path, 'r') as linkedin_export:
        print(f"parsing {file_path}")
        csvFile = [line for line in csv.reader(linkedin_export)]
        index = 0
        for idx, column in enumerate(csvFile[0]):
            MAPPING[column] = idx
        new_dates_for_location = 0
        newer_dates_for_location = 0
        for line in csvFile[1:]:
            (
                job, job_location, latest_job_location_posted_date, new_job, new_job_location,
                new_job_location_date_posted, l_new_dates_for_location, l_newer_dates_for_location
            ) = get_job_objects(line, daily_stat)
            new_dates_for_location += l_new_dates_for_location
            newer_dates_for_location += l_newer_dates_for_location

            labelling_job_location(line, job, latest_job_location_posted_date, new_job, new_job_location,
                                   new_job_location_date_posted, job_closed_list, applied_list, archived_list,
                                   resurfaced_applied_or_closed_list, resurfaced_in_case_list)

            if new_job_location and job_location.get_latest_job_location_posted_date_obj() is not None:
                if daily_stat.earliest_date_for_new_job_location > job_location.get_latest_job_location_posted_date_pst():
                    daily_stat.earliest_date_for_new_job_location = job_location.get_latest_job_location_posted_date_pst()
            jobs_updated_so_far.append(job.id)
            index += 1
            print(
                f"parsing new job at line {index}/{len(csvFile)} "
                f"{daily_stat.number_of_new_jobs} new jobs, {new_dates_for_location} new dates and"
                f" {newer_dates_for_location} newer dates and {daily_stat.number_of_new_job_locations} new job "
                f"locations so far"
            )

        print(f"parsed {file_path}")
        daily_stat.save()


def get_job_objects(line, daily_stat):
    new_dates_for_location = 0
    newer_dates_for_location = 0
    new_job = False
    new_job_location_date_posted = False
    job_location = JobLocation.objects.all().filter(
        job_board_id=line[MAPPING[JOB_ID_KEY]],
        location=line[MAPPING[LOCATION_KEY]],
        job_board_link=line[MAPPING[JOB_URL_KEY]],
        experience_level=ExperienceLevel.get_experience_number_from_csv(line[MAPPING[EXPERIENCE_LEVEL_KEY]]),
        job_board=line[MAPPING[JOB_BOARD]],
        easy_apply=line[MAPPING[IS_EASY_APPLY_KEY]] == TRUE_String,
        job_posting__job_title=line[MAPPING[JOB_TITLE_KEY]],
        job_posting__company_name=line[MAPPING[COMPANY_NAME_KEY]]
    ).first()
    new_job_location = job_location is None
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
            new_job = True
            daily_stat.number_of_new_jobs += 1
        job_location = JobLocation(
            job_posting=job,
            job_board_id=line[MAPPING[JOB_ID_KEY]],
            location=line[MAPPING[LOCATION_KEY]],
            job_board_link=line[MAPPING[JOB_URL_KEY]],
            experience_level=ExperienceLevel.get_experience_number_from_csv(line[MAPPING[EXPERIENCE_LEVEL_KEY]]),
            job_board=line[MAPPING[JOB_BOARD]],
            easy_apply=line[MAPPING[IS_EASY_APPLY_KEY]] == TRUE_String
        )
        job_location.save()

        JobLocationDailyStat(
            daily_stat=daily_stat,
            job_location=job_location
        ).save()

    date_from_csv = pstdatetime.from_csv_epoch(int(line[MAPPING[POST_DATE_KEY]]))
    if date_from_csv is not None:
        date_from_csv = date_from_csv.pst
    latest_job_location_posted_date = job_location.joblocationdateposted_set.all().order_by('-date_posted').first()
    if latest_job_location_posted_date is None:
        new_dates_for_location += 1
        latest_job_location_posted_date = JobLocationDatePosted(
            date_posted=date_from_csv,
            job_location_posting=job_location
        )
        latest_job_location_posted_date.save()
        new_job_location_date_posted = True
    elif date_from_csv is None:
        raise Exception(f"somehow there was no date in the csv for job {line[MAPPING[JOB_URL_KEY]]}")
    elif latest_job_location_posted_date.date_posted.pst < date_from_csv:
        newer_dates_for_location += 1
        latest_job_location_posted_date = JobLocationDatePosted(
            date_posted=date_from_csv,
            job_location_posting=job_location
        )
        latest_job_location_posted_date.save()
        new_job_location_date_posted = True

    job = job_location.job_posting
    return (job, job_location, latest_job_location_posted_date, new_job, new_job_location, new_job_location_date_posted,
            new_dates_for_location, newer_dates_for_location)


def labelling_job_location(line, job, latest_job_location_posted_date, new_job, new_job_location,
                           new_job_location_date_posted, job_closed_list, applied_list, archived_list,
                           resurfaced_applied_or_closed_list, resurfaced_in_case_list):
    archived_item = job.jobitem_set.all().filter(list__name=ARCHIVED_LIST_NAME).first()
    if archived_item is not None:
        # job was archived by the user already
        if new_job or new_job_location or new_job_location_date_posted:
            # this is necessary to make sure that if a job that is marked as archived but has a new job location
            # or a new job location date posted, then it is put back into the inbox
            archived_item.delete()
        else:
            # if a current job posting doesn't have a label except for Archived and (Job Closed or Job Applied)
            # it needs to be resurfaced to a special inbox to ensure that the application has not been re-opened
            job_in_non_archived_list = job.jobitem_set.all().exclude(list__name=ARCHIVED_LIST_NAME).count() > 0
            for job_location in job.joblocation_set.all():
                latest_job_location_is_marked_as_applied_or_closed = (
                    job_location.get_latest_job_location_posted_date_obj().joblocationdateposteditem_set.all().count() > 0
                )
                if job_in_non_archived_list:
                    JobItem.objects.all().get_or_create(job=job, list=resurfaced_in_case_list)
                elif latest_job_location_is_marked_as_applied_or_closed:
                    JobItem.objects.all().get_or_create(job=job, list=resurfaced_applied_or_closed_list)

    job_marked_as_closed = line[MAPPING[JOB_CLOSED_KEY]] == TRUE_String
    job_location_is_marked_as_closed_in_csv(job_marked_as_closed, latest_job_location_posted_date, job_closed_list)
    job_marked_as_applied = line[MAPPING[APPLIED_TO_JOB_KEY]] != ""
    job_location_is_marked_as_applied_in_csv(job_marked_as_applied, latest_job_location_posted_date, applied_list)
    archive_closed_or_applied_job(job_marked_as_applied, job_marked_as_closed, new_job, new_job_location,
                                  new_job_location_date_posted, latest_job_location_posted_date, job, archived_list)


def job_location_is_marked_as_closed_in_csv(job_marked_as_closed, latest_job_location_posted_date, job_closed_list):
    if job_marked_as_closed:
        closed_job_location_item = latest_job_location_posted_date.joblocationdateposteditem_set.all().filter(
            list__name=JOB_CLOSED_LIST_NAME
        ).first()
        if closed_job_location_item is None:
            JobLocationDatePostedItem.objects.all().get_or_create(
                job_location_date_posted=latest_job_location_posted_date, list=job_closed_list,
                date_added=None
            )


def job_location_is_marked_as_applied_in_csv(job_marked_as_applied, latest_job_location_posted_date, applied_list):
    if job_marked_as_applied:
        applied_job_location_item = latest_job_location_posted_date.joblocationdateposteditem_set.all().filter(
            list__name=APPLIED_LIST_NAME
        ).first()
        if applied_job_location_item is None:
            JobLocationDatePostedItem.objects.all().get_or_create(
                job_location_date_posted=latest_job_location_posted_date, list=applied_list,
                date_added=None
            )


def archive_closed_or_applied_job(job_marked_as_applied, job_marked_as_closed, new_job, new_job_location,
                                  new_job_location_date_posted, latest_job_location_posted_date, job, archived_list):
    job_applied_or_closed = job_marked_as_applied or job_marked_as_closed
    new_job_or_location_or_reposted = new_job or new_job_location or new_job_location_date_posted
    job_posting_has_only_this_location = (
        latest_job_location_posted_date.job_location_posting.job_posting.joblocation_set.all().count() == 1
    )
    if job_applied_or_closed and not new_job_or_location_or_reposted and job_posting_has_only_this_location:
        archived_job_item = job.jobitem_set.all().filter(list__name=ARCHIVED_LIST_NAME).first()
        etl_job_item = job.jobitem_set.all().filter(list__name=ETL_UPDATED_LIST_NAME).first()
        if archived_job_item is None:
            JobItem.objects.all().get_or_create(job=job, list=archived_list)
        if etl_job_item is not None:
            JobItem.objects.all().filter(list__name=ETL_UPDATED_LIST_NAME).delete()