import csv
import datetime
import json
import math
import random
import re
import time

from bs4 import BeautifulSoup
from dateutil.tz import tz
from django.conf import settings
from django.core.management import BaseCommand
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver import FirefoxOptions
from selenium.webdriver.common.by import By

from jobs.csv_header import MAPPING
from jobs.management.commands.create_linkedin_exports_api import get_job_item
from jobs.models import JobLocation, ExperienceLevel
from jobs.setup_logger import Loggers

COMPANIES_TO_SKIP = ["Canonical", 'Aha!', 'Crossover', 'Clevertech']

logger = Loggers.get_logger()


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--headless',
            action='store_true',
            default=False
        )

    def handle(self, *args, **options):
        today = datetime.datetime.today().astimezone(tz.gettz('Canada/Pacific'))

        opts = FirefoxOptions()
        if options['headless']:
            opts.add_argument("--headless")
        driver = webdriver.Firefox(options=opts)
        driver.set_page_load_timeout(30)
        driver.get("https://www.linkedin.com/uas/login")
        driver.find_element(value='username').send_keys(settings.LINKEDIN_EMAIL)
        word = driver.find_element(value='password')
        word.send_keys(settings.LINKEDIN_PASSWORD)
        word.submit()
        time.sleep(30)
        page_loaded = (
            len(BeautifulSoup(driver.page_source, 'html.parser').findAll("span")) > 10
        )
        if not page_loaded:
            driver.quit()
            return
        exports = open(f'{today.strftime("%Y-%m-%d_%I-%M-%S_%p")}_linkedin_exports.csv', mode='w')
        exports_writer = csv.writer(exports, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        exports_writer.writerow(list(MAPPING.keys()))
        exports.flush()
        get_updates_for_tracked_jobs(driver, exports_writer, exports)
        driver.quit()


def get_updates_for_tracked_jobs(driver, exports_writer, exports):
    job_locations = JobLocation.objects.all().filter(job_posting__item__isnull=True)
    total_number_of_inbox_jobs = len(job_locations)
    number_of_inbox_job_locations_closed = 0
    number_of_inbox_jobs_closed = 0
    number_of_inbox_job_locations_already_applied = 0
    number_of_inbox_jobs_already_applied = 0
    index = 0
    unable_to_retrieve_jobs = 0
    jobs_still_open = 0
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
        success = False
        job_location = job_locations[index]
        last_error = None
        initial_time = time.perf_counter()
        latest_attempt_time = time.perf_counter()
        iteration = 1
        driver.get(job_location.linkedin_link)
        time.sleep(5)
        while (not success) and ((latest_attempt_time - initial_time) <= 64):
            try:
                latest_attempt_time = time.perf_counter()
                job_info_obj = get_job_info(driver)
                success, job_info = get_job_item(job_location.linkedin_id)
                if not job_info_obj[0]:
                    raise Exception(job_info_obj[12])
                if not success:
                    raise Exception()
                success = job_info_obj[0]
                job_title = job_info_obj[1]
                company_name = job_info_obj[4]
                location = job_info_obj[5]
                job_closed = job_info_obj[6]
                job_already_applied = job_info['date_applied']
                job_open_for_application = job_info_obj[8]
                easy_apply = job_info_obj[9]
                timestamp = job_info_obj[10]
                experience_level = job_info_obj[11]
                if company_name not in COMPANIES_TO_SKIP:
                    if job_closed or job_already_applied is not None:
                        exports_writer.writerow([
                            job_location.linkedin_id, job_title, company_name, timestamp, experience_level,
                            location, job_location.linkedin_link, job_already_applied, easy_apply, job_closed
                        ])
                        exports.flush()
                    if job_closed:
                        if job_location.job_posting.id not in jobs_processed_so_far:
                            number_of_inbox_jobs_closed+=1
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
                    if job_already_applied is not None:
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
                    if job_open_for_application:
                        jobs_still_open += 1
                    index += 1
            except Exception as e:
                last_error = e
                random_number_milliseconds = random.randint(0, 1000) / 1000
                logger.info(f"attempt {iteration} trying to get index {index}/{len(job_locations)}")
                driver.get(job_location.linkedin_link)
                time.sleep(math.pow(3, iteration) + random_number_milliseconds)
                latest_attempt_time = time.perf_counter()
            iteration += 1
        if not success:
            index += 1
            unable_to_retrieve_jobs += 1
        message = (
            f"Job [{index}] => "
            f"\n\tInbox Job Locations Closed = {number_of_inbox_job_locations_closed}, "
            f"\n\tInbox Jobs Closed = {number_of_inbox_jobs_closed}, "
            f"\n\tInbox Job Locations Already Applied = {number_of_inbox_job_locations_already_applied}, "
            f"\n\tInbox Jobs Already Applied = {number_of_inbox_jobs_already_applied}, "
            f"\n\tJobs Still Open = {jobs_still_open}, "
            f"\n\tJobs Unable to Retrieve = {unable_to_retrieve_jobs}, "
            f"\n\tJobs Already Processed in Scrape = {jobs_already_processed_in_scrape}, "
            f"\n\tJob Links Reused for New Posting = {job_links_reused_for_new_posting} "
            f"/ {total_number_of_inbox_jobs}"
            f" for existing url {job_location.linkedin_link}"
        )
        if success:
            logger.info(message)
        else:
            logger.error(
                f"{message} due to an error\n{last_error}"
            )
        jobs_processed_so_far.append(job_location.job_posting.id)
    logger.info(json.dumps(stats, indent=4))


def get_job_info(driver, job_info_item=None):
    job_title = None
    company_name = None
    timestamp = None
    location = None
    job_link = None
    job_id = None
    job_closed = None
    job_already_applied = None
    job_open_for_application = None
    easy_apply = None
    experience_level = None
    errors = []
    if job_info_item is None:
        job_title_element = get_obj(driver, "jobs-unified-top-card__primary-description")
        if job_title_element is None:
            errors.append("Unable to get the job title")
        else:
            job_title = job_title_element.text.strip()

        company_and_location_and_date_posted_element = get_obj(driver, "jobs-unified-top-card__primary-description")
        if company_and_location_and_date_posted_element is None:
            errors.append("Unable to get the div that contains company name, location and the date the job was posted")
        else:
            company_and_location_and_date_posted_string = company_and_location_and_date_posted_element.text.strip()

            company_name = company_and_location_and_date_posted_string.split("·")[0].strip()

            timestamp, dividing_index = get_posted_date(driver)
            timestamp = timestamp.timestamp()

            location_and_timestamp = company_and_location_and_date_posted_string.split("·")[1]
            potentialIndexOfRepostedWord = location_and_timestamp[:dividing_index].rfind(" ")
            ending_index = potentialIndexOfRepostedWord \
                if location_and_timestamp[potentialIndexOfRepostedWord:dividing_index].strip().lower() == 'reposted' \
                else dividing_index
            location = location_and_timestamp[:ending_index].strip()
        experience_level = get_experience_level(driver)
    else:
        job_title = job_info_item.contents[1].text.replace("\n", "").strip()

        company_name = job_info_item.contents[3].text.replace("\n", "").strip()

        timestamp = get_posted_date(driver)[0].timestamp()
        experience_level = get_experience_level(driver)

        location = job_info_item.contents[5].text.replace("\n", "").strip()

        job_link = (
            re.search(
                r"/jobs/view/\d*/",
                job_info_item.contents[1].contents[1].attrs["href"]
            )[0]
        )
        job_id = int(re.findall(r'\d+', job_link)[0])

    error_message = "Unable to get job details due to error[s]:\n"
    try:
        job_closed_or_applied_text = driver.find_element(
            by=By.CLASS_NAME, value='artdeco-inline-feedback__message'
        ).text
        job_closed = job_closed_or_applied_text == 'No longer accepting applications'
        job_already_applied = re.match(r"Applied \d* \w* ago",
                                       job_closed_or_applied_text) is not None
    except NoSuchElementException as e:
        errors.append(f"{e}")
        pass

    try:
        if not job_already_applied:
            job_already_applied = driver.find_element(
                by=By.CLASS_NAME, value='post-apply-timeline__entity'
            ).text.split("\n")[0] == 'Applied on company site'
    except NoSuchElementException as e:
        errors.append(f"{e}")

    try:
        apply_text = driver.find_element(by=By.CLASS_NAME,
                                         value="jobs-apply-button").text
        job_open_for_application = apply_text in ["Apply", 'Easy Apply']
        easy_apply = apply_text == "Easy Apply"
        if easy_apply:
            job_already_applied = False
    except NoSuchElementException as e:
        errors.append(f"{e}")

    job_status_detected = (
        (easy_apply is not None and job_open_for_application is not None) or
        (job_open_for_application is not None) or
        job_closed is not None or
        job_already_applied is not None
    )
    job_info_detected = (
        job_title is not None and company_name is not None and
        location is not None and timestamp is not None
    )
    if job_info_item is not None:
        job_info_detected = (
            job_info_detected and job_link is not None and job_id is not None
        )
    success = job_status_detected and job_info_detected
    if not job_status_detected:
        error_message += "\n".join(errors)

    return (
        success, job_title, job_link, job_id, company_name, location, job_closed, job_already_applied,
        job_open_for_application, easy_apply, timestamp, experience_level, error_message
    )


def get_obj(driver, class_name):
    element = None
    try:
        element = driver.find_element(
            by=By.CLASS_NAME, value=class_name
        )
    except NoSuchElementException:
        try:
            element = driver.find_element(
                by=By.CLASS_NAME, value=f"job-details-{class_name}"
            )
        except NoSuchElementException:
            pass
    return element


def get_posted_date(driver):
    primary_description = get_obj(driver, "jobs-unified-top-card__primary-description")
    if primary_description is None:
        message = (
            "cannot find the datetime for a primary description because the class names seem to have"
            " changed"
        )
        logger.error(message)
        raise Exception(message)
    try:
        location_and_posted_date = primary_description.text.split(" · ")[1]
    except Exception as e:
        logger.error(
            "cannot find the datetime for a primary "
            f"description of [{primary_description}] due to error\n{e}"
        )
        raise Exception(primary_description)
    dividing_index = len(location_and_posted_date)
    word_index = 0
    while word_index <= 3:
        dividing_index = location_and_posted_date[:dividing_index].rfind(" ")
        word_index += 1
    try:
        date_posted = location_and_posted_date[dividing_index:].strip()
    except Exception as e:
        logger.error(
            "cannot find the datetime for a primary "
            f"description of [{location_and_posted_date}] due to error\n{e}"
        )
        raise Exception(location_and_posted_date)
    post_date = datetime.datetime.now(
        tz=tz.gettz('Canada/Pacific')
    ).replace(second=0).replace(microsecond=0)
    duration = int(date_posted[:date_posted.find(" ")])
    if 'year' in date_posted:
        post_date -= datetime.timedelta(days=(365 * duration))
        post_date = post_date.replace(hour=0).replace(minute=0)
    elif 'month' in date_posted:
        post_date -= datetime.timedelta(days=(30 * duration))
        post_date = post_date.replace(hour=0).replace(minute=0)
    elif 'week' in date_posted:
        post_date -= datetime.timedelta(days=(7 * duration))
        post_date = post_date.replace(hour=0).replace(minute=0)
    elif 'day' in date_posted:
        post_date -= datetime.timedelta(days=duration)
        post_date = post_date.replace(hour=0).replace(minute=0)
    elif 'hour' in date_posted:
        post_date -= datetime.timedelta(hours=duration)
        post_date = post_date.replace(minute=0)
    elif 'minute' in date_posted:
        post_date -= datetime.timedelta(minutes=duration)
    else:
        logger.error(
            "cannot find the datetime for date_posted "
            f"[{date_posted}] as it doesn't contain a time indicator"
        )
        raise Exception(date_posted)
    return post_date, dividing_index


def get_experience_level(driver):
    experience_level = get_obj(driver, "jobs-unified-top-card__job-insight")
    if experience_level is None:
        raise Exception("Unable to get experience level")
    else:
        experience_level_str = experience_level.text
        endingStr = experience_level_str.find("·")
        if endingStr != -1:
            experience_level_str = (experience_level_str[endingStr+2:]).strip().replace(" ", "_").replace("-", "_")
            return getattr(ExperienceLevel, experience_level_str).value
        else:
            return None