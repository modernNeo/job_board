import csv
import datetime
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

from jobs.models import JobLocation
from jobs.setup_logger import Loggers

COMPANIES_TO_SKIP = ["Canonical", 'Aha!', 'Crossover']

logger = Loggers.get_logger()


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--headless',
            action='store_true',
            default=False
        )

    def handle(self, *args, **options):
        status_file_name = 'linkedin_scrape_in_progress'
        # open(status_file_name, 'x')
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
            os.remove(status_file_name)
            return
        exports = open(f'{today.strftime("%Y-%m-%d_%I-%M-%S_%p")}_linkedin_exports.csv', mode='w')
        exports_writer = csv.writer(exports, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        exports_writer.writerow(
            ["jobId", "jobTitle", "companyName", "postDate", "location", "jobUrl", "applied", "isEasyApply", "closed"]
        )

        time_run = {}
        search_filter_time1 = get_updates_for_tracked_jobs(driver, exports_writer, exports)
        search_filter_time2 = time.perf_counter()
        time_run["existing_jobs_processed"] = search_filter_time2 - search_filter_time1

        time_run = get_new_jobs(driver, exports_writer, exports, time_run)
        time2 = time.perf_counter()
        logger.info(f"run time = {get_time_string(time2 - time1)}")
        for key, value in time_run.items():
            logger.info(f" {key} run time = {get_time_string(value)}")

        driver.quit()
        os.remove(status_file_name)


def get_updates_for_tracked_jobs(driver, exports_writer, exports):
    job_links = JobLocation.objects.all().filter(job_posting__item__isnull=True)
    total_number_of_inbox_jobs = len(job_links)
    number_of_jobs_closed_or_already_applied = 0
    index = 0
    unable_to_retrieve_jobs = 0
    jobs_still_open = 0
    search_filter_time1 = time.perf_counter()
    while index < len(job_links):
        job = job_links[index]
        initial_time = time.perf_counter()
        latest_attempt_time = time.perf_counter()
        success = False
        iteration = 1
        driver.get(job.linkedin_link)
        time.sleep(5)
        while (not success) and ((latest_attempt_time - initial_time) <= 64):
            try:
                latest_attempt_time = time.perf_counter()
                job_info_obj = get_job_info(driver)
                if not job_info_obj[0]:
                    raise Exception()
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
                            job.linkedin_id, job_title, company_name, timestamp, location,
                            job.linkedin_link, job_already_applied, easy_apply, job_closed
                        ])
                        exports.flush()
                        number_of_jobs_closed_or_already_applied += 1
                    if job_open_for_application:
                        jobs_still_open += 1
                    logger.info(
                        f"parsed job[{index + 1}] => Inbox Jobs Closed Or Already Applied = "
                        f"{number_of_jobs_closed_or_already_applied}, "
                        f"Jobs Unable to Retrieve = {unable_to_retrieve_jobs}, "
                        f"Jobs Still Open = {jobs_still_open} / {total_number_of_inbox_jobs}"
                        f" for existing url {job.linkedin_link}",
                    )
                    index += 1
            except Exception:
                random_number_milliseconds = random.randint(0, 1000) / 1000
                logger.info(f"attempt {iteration} trying to get index {index}/{len(job_links)}")
                driver.get(job.linkedin_link)
                time.sleep(math.pow(3, iteration) + random_number_milliseconds)
                latest_attempt_time = time.perf_counter()
            iteration += 1
        if not success:
            index += 1
            unable_to_retrieve_jobs += 1
            logger.error(
                f"parsed job[{index + 1}] => Jobs Processed = {number_of_jobs_closed_or_already_applied}, "
                f"Jobs Unable to Retrieve = {unable_to_retrieve_jobs}, "
                f"Jobs Still Open = {jobs_still_open} / {total_number_of_inbox_jobs}"
                f" for existing url {job.linkedin_link} due to an error\n"
            )
    return search_filter_time1


def get_new_jobs(driver, exports_writer, exports, time_run):
    EXPERIENCE_LEVEL_FILTER = "f_E=2%2C3%2C4"
    FT_OR_CONTRACT_FILTER = "f_JT=F%2CC"
    FILTER_FOR_ALL_JOBS = f"{EXPERIENCE_LEVEL_FILTER}&{FT_OR_CONTRACT_FILTER}"
    REMOTE_FILTER = "f_WT=2"
    WFH_AND_REMOTE_FILTER = f"{REMOTE_FILTER}%2C3"
    JAVA_KEYWORD = "keywords=intermediate%20java%20developer"
    SOFTWARE_KEYWORD = "keywords=intermediate%20software%20developer"
    CANADA = "location=Canada"
    VANCOUVER = "location=Vancouver%2C%20British%20Columbia%2C%20Canada"
    search_filters = [
        f"{FILTER_FOR_ALL_JOBS}&{CANADA}&{JAVA_KEYWORD}&{REMOTE_FILTER}",
        f"{FILTER_FOR_ALL_JOBS}&{CANADA}&{SOFTWARE_KEYWORD}&{REMOTE_FILTER}",
        f"{FILTER_FOR_ALL_JOBS}&{VANCOUVER}&{JAVA_KEYWORD}",
        f"{FILTER_FOR_ALL_JOBS}&{VANCOUVER}&{SOFTWARE_KEYWORD}"
    ]
    for search_filter in search_filters:
        logger.info(f"searching using {search_filter}")
        search_filter_time1 = time.perf_counter()
        more_jobs_to_search = True
        page = 0
        number_of_jobs_closed_or_already_applied = 0
        unable_to_retrieve_jobs = 0
        jobs_from_companies_to_skip = 0
        while more_jobs_to_search:
            url = f"https://www.linkedin.com/jobs/search/?{search_filter}&refresh=true&sortBy=DD"
            if page > 0:
                url += f"&start={25 * page}"
            logger.info(f"getting page {url} for page {(page + 1)}")
            page += 1
            more_jobs_to_search, total_number_of_inbox_jobs, jobs = load_page(driver, url, search_filter)
            if more_jobs_to_search:
                jobs_list = get_jobs(driver)
                index = 0
                number_of_job_on_current_page = len(jobs)
                while index < number_of_job_on_current_page:
                    logger.info(f"trying to get job at index {index} for {search_filter}")
                    job = jobs[index]
                    job.click()
                    success, job_info_item, error, jobs_list = get_job_item(
                        driver, jobs_list, index, job, number_of_job_on_current_page
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
                        if success:
                            if company_name not in COMPANIES_TO_SKIP:
                                exports_writer.writerow([
                                    job_id, job_title, company_name, timestamp,
                                    location, f"https://www.linkedin.com{job_link}", job_already_applied,
                                    easy_apply,
                                    job_closed
                                ])
                                exports.flush()
                                number_of_jobs_closed_or_already_applied += 1
                            else:
                                jobs_from_companies_to_skip += 1
                            logger.info(
                                f"Job {index}  => Parsed Jobs {number_of_jobs_closed_or_already_applied}, "
                                f"Jobs Unable to Retrieve = "
                                f"{unable_to_retrieve_jobs}, Skipped Companies = {jobs_from_companies_to_skip} / "
                                f"{total_number_of_inbox_jobs}\n"
                            )
                            index += 1
                        else:
                            unable_to_retrieve_jobs += 1
                            logger.error(
                                f"Job {index}  => Parsed Jobs {number_of_jobs_closed_or_already_applied}, "
                                f"Jobs Unable to Retrieve = "
                                f"{unable_to_retrieve_jobs}, Skipped Companies = {jobs_from_companies_to_skip} / "
                                f"{total_number_of_inbox_jobs} due to error\n{error}\n\n"
                            )
                            index += 1
                    else:
                        unable_to_retrieve_jobs += 1
                        logger.error(
                            f"Job {index}  => Parsed Jobs {number_of_jobs_closed_or_already_applied}, Jobs Unable to Retrieve = "
                            f"{unable_to_retrieve_jobs}, Skipped Companies = {jobs_from_companies_to_skip} / "
                            f"{total_number_of_inbox_jobs} due to error\n{error}\n\n"
                        )
                        index += 1
        search_filter_time2 = time.perf_counter()
        time_run[search_filter] = search_filter_time2 - search_filter_time1
    return time_run


def get_time_string(total_seconds):
    hours, minutes = 0, 0
    if total_seconds >= 60:
        minutes = int(int(total_seconds) / 60)
        if minutes >= 60:
            hours = int(int(minutes) / 60)
            minutes = minutes % 60
    seconds = int(total_seconds % 60)
    run_time_str = ""
    if hours > 0:
        if hours >= 10:
            run_time_str += f"{hours:{3}} "
        else:
            run_time_str += f"{hours:{2}} "
        run_time_str += "hours"
    if minutes > 0:
        if len(run_time_str) > 0:
            run_time_str += ","
        if seconds == 0 and hours > 0:
            run_time_str += " and "
        if minutes >= 10:
            run_time_str += f"{minutes:{3}} "
        else:
            run_time_str += f"{minutes:{2}} "
        run_time_str += "minutes"
    if seconds > 0:
        if len(run_time_str) > 0:
            run_time_str += ", and"
        if seconds >= 10:
            run_time_str += f"{seconds:{3}} "
        else:
            run_time_str += f"{seconds:{2}} "
        run_time_str += "seconds"
    if run_time_str == "":
        run_time_str = " 0 seconds"
    return run_time_str


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


def get_jobs(driver):
    return [
        item for item in BeautifulSoup(driver.page_source, 'html.parser').findAll("li")
        if 'class' in item.attrs and 'jobs-search-results__list-item' in item.attrs['class']
    ]


def load_page(driver, url, search_filter):
    driver.get(url)
    time.sleep(5)
    total_number_of_jobs = int(
        driver.find_element(
            by=By.CLASS_NAME, value='jobs-search-results-list__subtitle'
        ).text.split(" ")[0].replace(",", "")
    )
    try:
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
                raise Exception()
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
    job_open_for_application = None
    easy_apply = None
    job_title = None
    job_link = None
    job_id = None
    company_name = None
    location = None
    job_closed = None
    job_already_applied = None
    job_status_detected = False
    job_info_detected = False
    timestamp = None
    iteration = 0
    initial_time = time.perf_counter()
    latest_attempt_time = time.perf_counter()
    success = job_status_detected and job_info_detected
    if job_info_item is not None:
        job_title = job_info_item.contents[1].text.replace("\n", "").strip()
        job_link = (
            re.search(
                r"/jobs/view/\d*/",
                job_info_item.contents[1].contents[1].attrs["href"]
            )[0]
        )
        company_name = job_info_item.contents[3].text.replace("\n", "").strip()
        location = job_info_item.contents[5].text.replace("\n", "").strip()
        job_id = int(re.findall(r'\d+', job_link)[0])
        timestamp = get_posted_date(driver)[0].timestamp()
    else:
        job_title = driver.find_element(by=By.CLASS_NAME, value="jobs-unified-top-card__job-title").text.strip()
        company_and_location_and_date_posted_string = driver.find_element(
            by=By.CLASS_NAME, value="jobs-unified-top-card__primary-description"
        ).text.strip()
        company_name = company_and_location_and_date_posted_string.split("·")[0].strip()
        timestamp, dividing_index = get_posted_date(driver)
        timestamp = timestamp.timestamp()
        location_and_timestamp = company_and_location_and_date_posted_string.split("·")[1]
        potentialIndexOfRepostedWord = location_and_timestamp[:dividing_index].rfind(" ")
        if location_and_timestamp[potentialIndexOfRepostedWord:dividing_index].strip().lower() == 'reposted':
            location = location_and_timestamp[:potentialIndexOfRepostedWord].strip()
        else:
            location = location_and_timestamp[:dividing_index].strip()
    try:
        job_closed_or_applied_text = driver.find_element(
            by=By.CLASS_NAME, value='artdeco-inline-feedback__message'
        ).text
        job_closed = job_closed_or_applied_text == 'No longer accepting applications'
        job_already_applied = re.match(r"Applied \d* \w* ago",
                                       job_closed_or_applied_text) is not None
    except (NoSuchElementException, StaleElementReferenceException):
        pass
    try:
        if not job_already_applied:
            job_already_applied = driver.find_element(
                by=By.CLASS_NAME, value='post-apply-timeline__entity'
            ).text.split("\n")[0] == 'Applied on company site'
    except (NoSuchElementException, StaleElementReferenceException):
        pass
    try:
        apply_text = driver.find_element(by=By.CLASS_NAME,
                                         value="jobs-apply-button").text
        job_open_for_application = apply_text in ["Apply", 'Easy Apply']
        easy_apply = apply_text == "Easy Apply"
        if easy_apply:
            job_already_applied = False
    except (NoSuchElementException, StaleElementReferenceException):
        pass
    job_status_detected = (
        (job_open_for_application is not None) or
        (easy_apply is not None and job_open_for_application is not None) or
        job_closed is not None or
        job_already_applied is not None
    )
    if job_info_item is not None:
        job_info_detected = (
            job_title is not None and job_link is not None and job_id is not None and company_name is not None and
            location is not None and timestamp is not None
        )
    else:
        job_info_detected = (
            job_title is not None and company_name is not None and
            location is not None and timestamp is not None
        )
    success = job_status_detected and job_info_detected
    return (
        success, job_title, job_link, job_id, company_name, location, job_closed, job_already_applied,
        job_open_for_application, easy_apply, timestamp
    )
