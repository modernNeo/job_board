import csv
import datetime
import json
import math
import random
import re
import time

import requests
from bs4 import BeautifulSoup
from dateutil.tz import tz
from django.conf import settings
from django.core.management import BaseCommand

from jobs.csv_header import MAPPING
from jobs.models import JobLocation
from jobs.setup_logger import Loggers

COMPANIES_TO_SKIP = ["Canonical", 'Aha!', 'Crossover', 'Clevertech']

logger = Loggers.get_logger()

header = {
    "csrf-token": settings.AJAX,
    "Cookie": f"li_at={settings.LI_AT}; JSESSIONID={settings.AJAX}"
}


class Command(BaseCommand):

    def handle(self, *args, **options):
        today = datetime.datetime.today().astimezone(tz.gettz('Canada/Pacific'))

        exports = open(f'{today.strftime("%Y-%m-%d_%I-%M-%S_%p")}_linkedin_exports.csv', mode='w')
        exports_writer = csv.writer(exports, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        exports_writer.writerow(
            list(MAPPING.keys())
        )
        exports.flush()

        get_new_jobs(exports_writer, exports)


def get_new_jobs(exports_writer, exports):
    INTERN_EXPERIENCE_LEVEl = "1"
    ENTRY_EXPERIENCE_LEVEL = "2"
    ASSOCIATE_EXPERIENCE_LEVEL = "3"
    MID_SENIOR_EXPERIENCE_LEVEL = "4"
    DIRECTOR_LEVEL = "5"
    EXPERIENCE_LEVEL_FILTER = "f_E=" + "%2C".join(
        [ENTRY_EXPERIENCE_LEVEL, ASSOCIATE_EXPERIENCE_LEVEL, MID_SENIOR_EXPERIENCE_LEVEL]
    )

    FULL_TIME_JOB = "F"
    PART_TIME_JOB = "P"
    CONTRACT_JOB = "C"
    TEMPORARY_JOB = "T"
    INTERNSHIP = "I"
    JOB_TYPE_FILTER = "f_JT=" + "%2C".join(
        [FULL_TIME_JOB, CONTRACT_JOB]
    )

    FILTER_FOR_ALL_JOBS = f"{EXPERIENCE_LEVEL_FILTER}&{JOB_TYPE_FILTER}"

    ON_SITE_JOB = "1"
    REMOTE_JOB = "2"
    HYBRID_JOB = "3"
    FILTER_FOR_CANADA_JOBS = "f_WT=" + "%2C".join([REMOTE_JOB])

    JAVA_KEYWORD = "keywords=java%20developer"
    INTERMEDIATE_JAVA_KEYWORD = "keywords=intermediate%20java%20developer"
    SOFTWARE_KEYWORD = "keywords=intermediate%20software%20developer"
    CANADA = "location=Canada"
    VANCOUVER = "location=Vancouver%2C%20British%20Columbia%2C%20Canada"
    search_queries = {
        f"{FILTER_FOR_ALL_JOBS}&{CANADA}&{SOFTWARE_KEYWORD}&{FILTER_FOR_CANADA_JOBS}": "Canada Software Developer",
        f"{FILTER_FOR_ALL_JOBS}&{CANADA}&{JAVA_KEYWORD}&{FILTER_FOR_CANADA_JOBS}": "Canada Java Developer",
        f"{FILTER_FOR_ALL_JOBS}&{CANADA}&{INTERMEDIATE_JAVA_KEYWORD}&{FILTER_FOR_CANADA_JOBS}": "Canada Intermediate Java Developer",
        f"{FILTER_FOR_ALL_JOBS}&{VANCOUVER}&{SOFTWARE_KEYWORD}": "Vancouver Software Developer",
        f"{FILTER_FOR_ALL_JOBS}&{VANCOUVER}&{JAVA_KEYWORD}": "Vancouver Java Developer",
        f"{FILTER_FOR_ALL_JOBS}&{VANCOUVER}&{INTERMEDIATE_JAVA_KEYWORD}": "Vancouver Intermediate Java Developer",
    }

    all_jobs = {}
    overall_index = 0
    COMPANY_NAME_KEY = 'company_name'
    LINKEDIN_URN_KEY = 'linkedin_urn'
    for url_filter, human_readable_string in search_queries.items():
        logger.info(f"searching using {human_readable_string}")
        page = 0
        while page is not None:
            url = (
                f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search/"
                f"?{url_filter}&refresh=true&sortBy=DD"
            )
            print(f"getting page {page}")
            if page > 0:
                url += f"&start={25 * page}"
            jobs_list_bs4 = BeautifulSoup(requests.get(url).text, 'html.parser')
            job_posting_linkedin_ids = [
                job_posting_linkedin_id.contents[1].attrs['data-entity-urn'][18:]
                for job_posting_linkedin_id in jobs_list_bs4.findAll("li")
            ]
            job_posting_company_names = [
                company_name.text.replace("\n", "").strip()
                for company_name in jobs_list_bs4.findAll("h4")

            ]
            if len(job_posting_linkedin_ids) != len(job_posting_company_names):
                raise Exception(f"{len(job_posting_linkedin_ids)} =|= {len(job_posting_company_names)}")
            if len(job_posting_linkedin_ids) == 0:
                page = None
            else:
                current_jobs_dict = {
                    overall_index+index: {
                        COMPANY_NAME_KEY: job_posting_company_names[index],
                        LINKEDIN_URN_KEY: linkedin_id
                     }
                    for index, linkedin_id in enumerate(job_posting_linkedin_ids)
                }
                overall_index += len(job_posting_company_names)
                all_jobs.update(current_jobs_dict)
                page += 1
    number_of_jobs = len(all_jobs)
    processed_job_index = 0
    all_jobs = all_jobs.values()
    processed_ids = []
    for indx, job_snippet in enumerate(all_jobs):
        company_name = job_snippet[COMPANY_NAME_KEY]
        if company_name not in COMPANIES_TO_SKIP:
            job_id = job_snippet[LINKEDIN_URN_KEY]
            if job_id not in processed_ids:
                processed_ids.append(job_id)
                processed_job_index += 1
                success, job_info = get_job_item(job_id)
                if success:
                    job_title = job_info['job_title']
                    location = job_info['location']
                    date_applied = job_info['date_applied']
                    easy_apply = job_info['easy_apply']
                    timestamp = job_info['timestamp']
                    experience_level = job_info['experience_level']
                    exports_writer.writerow([
                        job_id, job_title, company_name, timestamp, experience_level, location,
                        f"https://www.linkedin.com/jobs/view/{job_id}/", date_applied, easy_apply, None
                    ])
                    exports.flush()
                print(f"parsed job {processed_job_index} out of {indx+1}/{number_of_jobs}")
            else:
                logger.error(f"skipping duplicate job of {indx+1}/{number_of_jobs}")
        else:
            logger.error(f"skipping job {indx+1}/{number_of_jobs}")


def get_job_item(job_id):
    successful = False
    initial_attempt_time = time.perf_counter()
    latest_attempt_time = time.perf_counter()
    iteration = 1
    response = None
    while (not successful) and ((latest_attempt_time - initial_attempt_time) <= 64):
        try:
            response = requests.get(
                f"https://www.linkedin.com/voyager/api/jobs/jobPostings/{job_id}",
                headers=header
            )
            successful = response.status_code == 200
            if response.status_code != 200:
                if response.text == 'CSRF check failed.':
                    print("you need to update the cookies")
                    exit(1)
                raise Exception()
        except Exception:
            random_number_milliseconds = random.randint(0, 1000) / 1000
            logger.info(f"attempt {iteration} trying to get linkedin_id {job_id}")
            time.sleep(math.pow(3, iteration) + random_number_milliseconds)
            latest_attempt_time = time.perf_counter()
        iteration += 1
    if successful:
        job_info = json.loads(response.text)
        job_title = job_info['title']
        location = job_info['formattedLocation']
        date_applied = int(int(job_info['applyingInfo']['appliedAt'])/1000) if job_info['applyingInfo']['applied'] else None
        easy_apply = 'com.linkedin.voyager.jobs.ComplexOnsiteApply' in job_info['applyMethod']
        timestamp = job_info['createdAt']
        experience_level = job_info['formattedExperienceLevel'].replace(" ", "_").replace("-", "_")
        job_info = {
            "job_title": job_title, "location": location,
            "date_applied": date_applied, "easy_apply": easy_apply, "timestamp": timestamp,
            "experience_level": experience_level
        }
    else:
        job_info = None
    return successful, job_info


def get_updates_for_tracked_jobs(exports_writer, exports, new_jobs):
    job_locations = JobLocation.objects.all().filter(job_posting__item__isnull=True)
    total_number_of_inbox_jobs = len(job_locations)
    number_of_inbox_job_locations_closed = 0
    number_of_inbox_jobs_closed = 0
    number_of_inbox_job_locations_already_applied = 0
    number_of_inbox_jobs_already_applied = 0
    index = 0
    unable_to_retrieve_jobs = 0
    jobs_already_processed_in_scrape = 0
    job_links_reused_for_new_posting = 0
    jobs_processed_so_far = []
    stats = {
        "number_of_inbox_job_locations_closed" : [],
        "number_of_inbox_jobs_closed" : [],
        "number_of_inbox_job_locations_already_applied" : [],
        "number_of_inbox_jobs_already_applied" : []
    }
    while index < len(job_locations):
        job_location = job_locations[index]
        if job_location.linkedin_id in new_jobs:
            if f"{job_location.job_posting.company_name}_{job_location.job_posting.job_title}" == new_jobs[job_location.linkedin_id]['job_posting']:
                if job_location.job_posting.id not in jobs_processed_so_far:
                    # job postings
                    if new_jobs[job_location.linkedin_id]['job_already_applied']:
                        number_of_inbox_jobs_already_applied += 1
                        stats['number_of_inbox_jobs_already_applied'].append({
                            "id": job_location.job_posting.id,
                            "company_name": job_location.job_posting.company_name,
                            "job_title": job_location.job_posting.job_title,
                            "linkedin_id": job_location.linkedin_id
                        })
                    if new_jobs[job_location.linkedin_id]['job_closed']:
                        number_of_inbox_jobs_closed += 1
                        stats['number_of_inbox_jobs_closed'].append({
                            "id": job_location.job_posting.id,
                            "company_name": job_location.job_posting.company_name,
                            "job_title": job_location.job_posting.job_title,
                            "linkedin_id": job_location.linkedin_id
                        })
                if new_jobs[job_location.linkedin_id]['job_already_applied']:
                    number_of_inbox_job_locations_already_applied += 1
                    stats['number_of_inbox_job_locations_already_applied'].append({
                        "id": job_location.id,
                        "company_name": job_location.job_posting.company_name,
                        "job_title": job_location.job_posting.job_title,
                        "linkedin_id": job_location.linkedin_id
                    })
                if new_jobs[job_location.linkedin_id]['job_closed']:
                    number_of_inbox_job_locations_closed += 1
                    stats['number_of_inbox_job_locations_closed'].append({
                        "id": job_location.id,
                        "company_name": job_location.job_posting.company_name,
                        "job_title": job_location.job_posting.job_title,
                        "linkedin_id": job_location.linkedin_id
                    })
                jobs_already_processed_in_scrape += 1
                index += 1
            else:
                job_links_reused_for_new_posting += 1
                if job_location.job_posting.id not in jobs_processed_so_far:
                    number_of_inbox_jobs_closed += 1
                    stats['number_of_inbox_jobs_closed'].append({
                        "id": job_location.job_posting.id,
                        "company_name": job_location.job_posting.company_name,
                        "job_title": job_location.job_posting.job_title,
                        "linkedin_id": job_location.linkedin_id
                    })
                number_of_inbox_job_locations_closed += 1
                stats['number_of_inbox_job_locations_closed'].append({
                    "id": job_location.id,
                    "company_name": job_location.job_posting.company_name,
                    "job_title": job_location.job_posting.job_title,
                    "linkedin_id": job_location.linkedin_id
                })
                index += 1
                exports_writer.writerow([
                    job_location.linkedin_id, job_location.job_posting.job_title, job_location.job_posting.company_name,
                    job_location.date_posted, job_location.experience_level, job_location.location,
                    job_location.linkedin_link, None, None, True
                ])
                exports.flush()
        else:
            success, job_info = get_job_item(job_location.linkedin_id)
            if success:
                job_title = job_info['job_title']
                location = job_info['location']
                date_applied = job_info['date_applied']
                easy_apply = job_info['easy_apply']
                timestamp = job_info['timestamp']
                experience_level = job_info['experience_level']
                if date_applied is not None:
                    exports_writer.writerow([
                        job_location.linkedin_id, job_title, job_location.job_posting.company_name, timestamp,
                        experience_level, location, job_location.linkedin_link, date_applied, easy_apply
                    ])
                    exports.flush()
                if date_applied is not None:
                    if job_location.job_posting.id not in jobs_processed_so_far:
                        number_of_inbox_jobs_already_applied+=1
                        stats['number_of_inbox_jobs_already_applied'].append({
                            "id": job_location.job_posting.id,
                            "company_name": job_location.job_posting.company_name,
                            "job_title": job_location.job_posting.job_title,
                            "linkedin_id": job_location.linkedin_id
                        })
                    number_of_inbox_job_locations_already_applied += 1
                    stats['number_of_inbox_job_locations_already_applied'].append({
                        "id": job_location.id,
                        "company_name": job_location.job_posting.company_name,
                        "job_title": job_location.job_posting.job_title,
                        "linkedin_id": job_location.linkedin_id
                    })
            else:
                unable_to_retrieve_jobs+=1
            index += 1
        logger.info(
            f"Job [{index}] => "
            f"\n\tInbox Job Locations Already Applied = {number_of_inbox_job_locations_already_applied}, "
            f"\n\tInbox Jobs Already Applied = {number_of_inbox_jobs_already_applied}, "
            f"\n\tJobs Unable to Retrieve = {unable_to_retrieve_jobs}, "
            f"\n\tJobs Already Processed in Scrape = {jobs_already_processed_in_scrape}, "
            f"\n\tJob Links Reused for New Posting = {job_links_reused_for_new_posting} "
            f"/ {total_number_of_inbox_jobs}"
            f" for existing url {job_location.linkedin_link}"
        )
        jobs_processed_so_far.append(job_location.job_posting.id)
    logger.info(json.dumps(stats, indent=4))
