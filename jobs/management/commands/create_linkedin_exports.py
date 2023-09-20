import csv
import datetime
import json
import math
import os
import random
import re
import time

from bs4 import BeautifulSoup
from dateutil.tz import tz
from django.conf import settings
from django.core.management import BaseCommand
from selenium import webdriver
from selenium.common import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver import FirefoxOptions
from selenium.webdriver.common.by import By

from jobs.csv_header import MAPPING
from jobs.models import JobLocation
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
        time1 = time.perf_counter()
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
        exports_writer.writerow(
            list(MAPPING.keys())
        )
        exports.flush()

        time_run = {}
        time_run, new_jobs = get_new_jobs(driver, exports_writer, exports, time_run)
        search_filter_time1 = time.perf_counter()
        get_updates_for_tracked_jobs(driver, exports_writer, exports, new_jobs)
        search_filter_time2 = time.perf_counter()
        time_run["existing_jobs_processed"] = search_filter_time2 - search_filter_time1

        time2 = time.perf_counter()
        exports_writer.writerow(
            ["export_type", "run time [seconds]"]
        )
        exports_writer.writerow(["overall_task", time2-time1])
        exports.flush()

        for key, value in time_run.items():
            exports_writer.writerow([key, value])
            exports.flush()

        driver.quit()


def get_new_jobs(driver, exports_writer, exports, time_run):
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

    JAVA_KEYWORD = "keywords=intermediate%20java%20developer"
    SOFTWARE_KEYWORD = "keywords=intermediate%20software%20developer"
    CANADA = "location=Canada"
    VANCOUVER = "location=Vancouver%2C%20British%20Columbia%2C%20Canada"
    search_queries = {
        f"{FILTER_FOR_ALL_JOBS}&{CANADA}&{SOFTWARE_KEYWORD}&{FILTER_FOR_CANADA_JOBS}": "Canada Software Developer",
        f"{FILTER_FOR_ALL_JOBS}&{CANADA}&{JAVA_KEYWORD}&{FILTER_FOR_CANADA_JOBS}": "Canada Java Developer",
        f"{FILTER_FOR_ALL_JOBS}&{VANCOUVER}&{SOFTWARE_KEYWORD}": "Vancouver Software Developer",
        f"{FILTER_FOR_ALL_JOBS}&{VANCOUVER}&{JAVA_KEYWORD}": "Vancouver Java Developer",
    }
    new_jobs = {}
    number_of_jobs_added_to_csv = 0
    jobs_from_companies_to_skip = 0
    unable_to_retrieve_jobs = 0
    unclickable_jobs = 0
    for url_filter, human_readable_string in search_queries.items():
        logger.info(f"searching using {human_readable_string}")
        search_filter_time1 = time.perf_counter()
        more_jobs_to_search = True
        page = 0
        number_of_jobs_added_to_csv_for_current_filter = 0
        while more_jobs_to_search:
            url = f"https://www.linkedin.com/jobs/search/?{url_filter}&refresh=true&sortBy=DD"
            if page > 0:
                url += f"&start={25 * page}"
            logger.info(f"getting page {url} for page {(page + 1)}")
            page += 1
            more_jobs_to_search, total_number_of_inbox_jobs, selenium_jobs_list = load_search_result_page(
                driver, url, url_filter
            )
            if more_jobs_to_search:
                bs4_jobs_list = get_jobs(driver)
                index = 0
                number_of_job_on_current_page = len(selenium_jobs_list)
                while index < number_of_job_on_current_page:
                    log_error = None
                    logger.info(f"trying to get job at index {index} for {human_readable_string}")
                    selenium_job = selenium_jobs_list[index]

                    # tries to perform a job click
                    successful_job_click = False
                    initial_job_click_time = time.perf_counter()
                    latest_job_click_attempt_time = time.perf_counter()
                    iteration = 1
                    click_on_job_error = None
                    while (not successful_job_click) and ((latest_job_click_attempt_time - initial_job_click_time) <= 64):
                        try:
                            selenium_job.click()
                            successful_job_click = True
                        except Exception as click_error:
                            random_number_milliseconds = random.randint(0, 1000) / 1000
                            logger.info(f"attempt {iteration} trying to get index {index}/{len(bs4_jobs_list)}")
                            try:
                                _, _, selenium_jobs_list = load_search_result_page(
                                    driver, url, url_filter
                                )
                                time.sleep(10)  # sleeping for 10 extra seconds just in case cause
                                # the code only goes here if there might already be some problems with LinkedIn
                                bs4_jobs_list = get_jobs(driver)
                                selenium_job = selenium_jobs_list[index]
                                driver.execute_script("arguments[0].scrollIntoView();", selenium_job)
                            except Exception as reload_error:
                                logger.error(
                                    f"Could not load any job {index} on page {url} even after a reload due to"
                                    f" error:\n{reload_error}\n\n"
                                )
                            time.sleep(math.pow(3, iteration) + random_number_milliseconds)
                            click_on_job_error = click_error
                            latest_job_click_attempt_time = time.perf_counter()
                        iteration += 1

                    if successful_job_click:
                        success, job_info_item, get_job_item_error, bs4_jobs_list = get_job_item(
                            driver, bs4_jobs_list, index, selenium_job, number_of_job_on_current_page
                        )
                        if success:
                            job_title = job_info_item[1]
                            job_link = job_info_item[2]
                            job_id = job_info_item[3]
                            company_name = job_info_item[4]
                            location = job_info_item[5]
                            job_closed = job_info_item[6]
                            job_already_applied = job_info_item[7]
                            easy_apply = job_info_item[9]
                            timestamp = job_info_item[10]
                            if company_name not in COMPANIES_TO_SKIP:
                                if job_id not in new_jobs:
                                    new_jobs[job_id] = {
                                        "job_posting": f"{company_name}_{job_title}",
                                        "job_already_applied": job_already_applied,
                                        "job_closed": job_closed

                                    }
                                exports_writer.writerow([
                                    job_id, job_title, company_name, timestamp,
                                    location, f"https://www.linkedin.com{job_link}", job_already_applied,
                                    easy_apply, job_closed
                                ])
                                exports.flush()
                                number_of_jobs_added_to_csv += 1
                                number_of_jobs_added_to_csv_for_current_filter += 1
                            else:
                                jobs_from_companies_to_skip += 1
                            index += 1
                        else:
                            unable_to_retrieve_jobs += 1
                            log_error = get_job_item_error
                            index += 1
                    else:
                        unclickable_jobs += 1
                        log_error = click_on_job_error
                        index += 1
                    message = (
                            f"Job {index}  => "
                            f"\n\tJobs Successfully Added to CSV For Current Filter = "
                            f"{number_of_jobs_added_to_csv_for_current_filter}, "
                            f"\n\tPage = {page} for filter {human_readable_string}, "
                            f"\n\tJobs Unable to Retrieve = {unable_to_retrieve_jobs}, "
                            f"\n\tJobs Unable to Click On = {unclickable_jobs}, "
                            f"\n\tSkipped Companies = {jobs_from_companies_to_skip} / "
                            f"{total_number_of_inbox_jobs}. "
                            f"\n\tTotal Number of Jobs Successfully Added to CSV So Far = {number_of_jobs_added_to_csv}"
                    )
                    if log_error is None:
                        logger.info(
                            f"{message}\n"
                        )
                    else:
                        logger.error(
                            f"{message} due to error\n{log_error}\n\n"
                        )
        search_filter_time2 = time.perf_counter()
        time_run[human_readable_string] = search_filter_time2 - search_filter_time1
    return time_run, new_jobs


def load_search_result_page(driver, url, search_filter):
    driver.get(url)
    time.sleep(5)
    try:
        total_number_of_jobs = int(
            driver.find_element(
                by=By.CLASS_NAME, value='jobs-search-results-list__subtitle'
            ).text.split(" ")[0].replace(",", "")
        )
        jobs = driver.find_element(
            by=By.CLASS_NAME, value='scaffold-layout__list-container'
        ).find_elements(
            by=By.XPATH, value=".//li[contains(@id, 'ember')]"
        )
        if jobs is None:
            return False, None, None
        return True, total_number_of_jobs, jobs
    except (NoSuchElementException, StaleElementReferenceException):
        logger.info(f"no more jobs to search for with filter {search_filter}")
        return False, None, None


def get_jobs(driver):
    return [
        item for item in BeautifulSoup(driver.page_source, 'html.parser').findAll("li")
        if 'class' in item.attrs and 'jobs-search-results__list-item' in item.attrs['class']
    ]


def get_job_item(driver, jobs_list, index, job, number_of_job_on_current_page):
    initial_time = time.perf_counter()
    latest_attempt_time = time.perf_counter()
    success = False
    latest_error = None
    iteration = 1
    job_info_obj = None
    while (not success) and ((latest_attempt_time - initial_time) <= 64):
        try:
            if index + 1 == number_of_job_on_current_page:
                driver.execute_script("arguments[0].scrollIntoView();", job)
            time.sleep(3)
            job_info_obj = get_job_info(
                driver,
                job_info_item=jobs_list[index].contents[1].contents[1].contents[1].contents[3]
            )
            if not job_info_obj[0]:
                raise Exception(job_info_obj[11])
            success = job_info_obj[0]
        except Exception as error:
            random_number_milliseconds = random.randint(0, 1000) / 1000
            logger.info(f"attempt {iteration} trying to get index {index}/{len(jobs_list)}")
            jobs_list = get_jobs(driver)
            driver.execute_script("arguments[0].scrollIntoView();", job)
            time.sleep(math.pow(3, iteration) + random_number_milliseconds)
            latest_error = error
            latest_attempt_time = time.perf_counter()
        iteration += 1
    if success:
        return True, job_info_obj, None, jobs_list
    else:
        return False, None, latest_error, jobs_list


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
    if job_info_item is None:
        job_title = driver.find_element(by=By.CLASS_NAME, value="jobs-unified-top-card__job-title").text.strip()

        company_and_location_and_date_posted_string = driver.find_element(
            by=By.CLASS_NAME, value="jobs-unified-top-card__primary-description"
        ).text.strip()
        company_name = company_and_location_and_date_posted_string.split("·")[0].strip()

        timestamp, dividing_index = get_posted_date(driver)
        timestamp = timestamp.timestamp()

        location_and_timestamp = company_and_location_and_date_posted_string.split("·")[1]
        potentialIndexOfRepostedWord = location_and_timestamp[:dividing_index].rfind(" ")
        ending_index = potentialIndexOfRepostedWord \
            if location_and_timestamp[potentialIndexOfRepostedWord:dividing_index].strip().lower() == 'reposted' \
            else dividing_index
        location = location_and_timestamp[:ending_index].strip()
    else:
        job_title = job_info_item.contents[1].text.replace("\n", "").strip()

        company_name = job_info_item.contents[3].text.replace("\n", "").strip()

        timestamp = get_posted_date(driver)[0].timestamp()

        location = job_info_item.contents[5].text.replace("\n", "").strip()

        job_link = (
            re.search(
                r"/jobs/view/\d*/",
                job_info_item.contents[1].contents[1].attrs["href"]
            )[0]
        )
        job_id = int(re.findall(r'\d+', job_link)[0])

    error_message = "Unable to get job details due to error[s]:\n"
    errors = []
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
        job_open_for_application, easy_apply, timestamp, error_message
    )


def get_updates_for_tracked_jobs(driver, exports_writer, exports, new_jobs):
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
                success = True
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
                    job_location.date_posted, job_location.location, job_location.linkedin_link, None, None, True
                ])
                exports.flush()
                success = True
        else:
            initial_time = time.perf_counter()
            latest_attempt_time = time.perf_counter()
            iteration = 1
            driver.get(job_location.linkedin_link)
            time.sleep(5)
            while (not success) and ((latest_attempt_time - initial_time) <= 64):
                try:
                    latest_attempt_time = time.perf_counter()
                    job_info_obj = get_job_info(driver)
                    if not job_info_obj[0]:
                        raise Exception(job_info_obj[11])
                    success = job_info_obj[0]
                    job_title = job_info_obj[1]
                    company_name = job_info_obj[4]
                    location = job_info_obj[5]
                    job_closed = job_info_obj[6]
                    job_already_applied = job_info_obj[7]
                    job_open_for_application = job_info_obj[8]
                    easy_apply = job_info_obj[9]
                    timestamp = job_info_obj[10]
                    if company_name not in COMPANIES_TO_SKIP:
                        if job_closed or job_already_applied:
                            exports_writer.writerow([
                                job_location.linkedin_id, job_title, company_name, timestamp, location,
                                job_location.linkedin_link, job_already_applied, easy_apply, job_closed
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
                        if job_already_applied:
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


def get_posted_date(driver):
    primary_description = driver.find_element(
        by=By.CLASS_NAME, value="jobs-unified-top-card__primary-description"
    )
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







