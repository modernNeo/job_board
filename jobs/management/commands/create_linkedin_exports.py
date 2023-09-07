import csv
import datetime
import os
import re
import time

from bs4 import BeautifulSoup
from dateutil.tz import tz
from django.conf import settings
from django.core.management import BaseCommand
from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver import FirefoxOptions
from selenium.webdriver.common.by import By

from jobs.models import Job
from jobs.setup_logger import Loggers

COMPANIES_TO_SKIP = ["Canonical", 'Aha!', 'Crossover']

logger = Loggers.get_logger()


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
        return False
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
        return False
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
    return post_date


def get_job(driver):
    return [
        item for item in BeautifulSoup(driver.page_source, 'html.parser').findAll("li")
        if 'class' in item.attrs and 'jobs-search-results__list-item' in item.attrs['class']
    ]


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--headless',
            action='store_true',
            default=False
        )

    def handle(self, *args, **options):
        status_file_name = 'linkedin_scrape_in_progress'
        open(status_file_name, 'x')
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
        jobs = Job.objects.all().filter(item__isnull=True)
        total_number_of_jobs = len(jobs)
        number_of_jobs_processed = 0
        retry_attempt_to_get_job_details = 0
        retry_max_to_get_job_details = 5
        search_filter_time1 = time.perf_counter()
        index = 0
        skipped_jobs = 0
        open_job = 0
        while index < len(jobs):
            job = jobs[index]
            job_access = False
            try:
                driver.get(job.linkedin_link)
                job_access = True
            except TimeoutException:
                if retry_attempt_to_get_job_details < retry_max_to_get_job_details:
                    retry_attempt_to_get_job_details += 1
                else:
                    index+=1
                    skipped_jobs+=1
                    logger.info(
                        f"parsed job[{index+1}] => Jobs Processed = {number_of_jobs_processed}, "
                        f"Skipped Jobs = {skipped_jobs}, Open Jobs = {open_job} / {total_number_of_jobs}"
                        f" for existing url {job.linkedin_link}              "
                    )
                    retry_attempt_to_get_job_details = 0
            if job_access:
                time.sleep(5)
                easy_apply = False
                job_already_applied = False
                job_closed = False
                job_closed_or_applied_text = None
                job_open_for_application = False
                try:
                    job_closed_or_applied_text = driver.find_element(
                        by=By.CLASS_NAME, value='artdeco-inline-feedback__message'
                    ).text
                    job_closed = job_closed_or_applied_text == 'No longer accepting applications'
                    job_already_applied = re.match(r"Applied \d* \w* ago", job_closed_or_applied_text) is not None
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
                    apply_text = driver.find_element(by=By.CLASS_NAME, value="jobs-apply-button").text
                    job_open_for_application = apply_text in ["Apply", 'Easy Apply']
                    easy_apply = apply_text == "Easy Apply"
                    if easy_apply:
                        job_already_applied = False
                except (NoSuchElementException, StaleElementReferenceException):
                    pass
                if not (job_closed or job_already_applied or job_open_for_application):
                    if retry_attempt_to_get_job_details < retry_max_to_get_job_details:
                        retry_attempt_to_get_job_details += 1
                    else:
                        index+=1
                        skipped_jobs+=1
                        logger.info(
                            f"parsed job[{index+1}] => Jobs Processed = {number_of_jobs_processed}, "
                            f"Skipped Jobs = {skipped_jobs}, Open Jobs = {open_job} / {total_number_of_jobs}"
                            f" for existing url {job.linkedin_link}"
                        )
                        retry_attempt_to_get_job_details = 0
                else:
                    timestamp = get_posted_date(driver)
                    if timestamp is False:
                        if retry_attempt_to_get_job_details < retry_max_to_get_job_details:
                            retry_attempt_to_get_job_details += 1
                        else:
                            index+=1
                            skipped_jobs+=1
                            logger.info(
                                f"parsed job[{index+1}] => Jobs Processed = {number_of_jobs_processed}, "
                                f"Skipped Jobs = {skipped_jobs}, Open Jobs = {open_job} / {total_number_of_jobs}"
                                f" for existing url {job.linkedin_link}",
                            )
                            retry_attempt_to_get_job_details = 0
                    elif job.organisation_name not in COMPANIES_TO_SKIP:
                        retry_attempt_to_get_job_details = 0
                        if job_closed or job_already_applied:
                            timestamp = timestamp.timestamp()
                            exports_writer.writerow([
                                job.linkedin_id, job.job_title, job.organisation_name, timestamp, job.location, job.linkedin_link,
                                job_already_applied, easy_apply, job_closed
                            ])
                            exports.flush()
                            number_of_jobs_processed += 1
                        if job_open_for_application:
                            open_job += 1
                        logger.info(
                            f"parsed job[{index+1}] => Jobs Processed = {number_of_jobs_processed}, "
                            f"Skipped Jobs = {skipped_jobs}, Open Jobs = {open_job} / {total_number_of_jobs}"
                            f" for existing url {job.linkedin_link}",
                        )
                        index+=1

        search_filter_time2 = time.perf_counter()
        time_run["existing_jobs_processed"] = search_filter_time2 - search_filter_time1

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
            search_filter_time1 = time.perf_counter()
            more_jobs_to_search = True
            page = 0
            total_number_of_jobs = None
            number_of_jobs_processed = 0
            skipped_jobs = 0
            while more_jobs_to_search:
                url = f"https://www.linkedin.com/jobs/search/?{search_filter}&refresh=true&sortBy=DD"
                if page > 0:
                    url += f"&start={25 * page}"
                logger.info(f"\ngetting page {url} for page {(page + 1)}")
                page += 1
                driver.get(url)

                time.sleep(5)
                jobs = None
                if total_number_of_jobs is None:
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
                except (NoSuchElementException, StaleElementReferenceException):
                    more_jobs_to_search = False
                if more_jobs_to_search and jobs is not None:
                    jobs_list = get_job(driver)
                    index = 0
                    retry_attempt_to_get_job_details = 0
                    retry_max_to_get_job_details = 5
                    while index < len(jobs):
                        job = jobs[index]
                        if retry_attempt_to_get_job_details == 0:
                            job.click()
                        time.sleep(4)
                        retry_max = 5
                        retry_attempt = 0
                        job_info_item = None
                        job_item_obtained = False
                        easy_apply = False
                        job_closed = False
                        job_already_applied = False
                        job_closed_or_applied_text = None
                        job_open_for_application = False
                        apply_text = None
                        while not (job_item_obtained or retry_attempt == retry_max):
                            try:
                                if retry_attempt > 0:
                                    logger.info(f"attempt {retry_attempt}/{retry_max} to get job info")
                                job_info_item = jobs_list[index].contents[1].contents[1].contents[1].contents[3]
                                job_item_obtained = True
                            except AttributeError:
                                driver.execute_script("arguments[0].scrollIntoView();", job)
                                time.sleep(4)
                                jobs_list = get_job(driver)
                                retry_attempt += 1
                        if job_info_item is not None:
                            job_title = job_info_item.contents[1].text.replace("\n", "").strip()
                            job_link = re.search(r"/jobs/view/\d*/", job_info_item.contents[1].contents[1].attrs["href"])[0]
                            job_id = int(re.findall(r'\d+', job_link)[0])
                            company_name = job_info_item.contents[3].text.replace("\n", "").strip()
                            location = job_info_item.contents[5].text.replace("\n", "").strip()
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
                            if not (job_closed or job_already_applied or job_open_for_application):
                                if retry_attempt_to_get_job_details < retry_max_to_get_job_details:
                                    retry_attempt_to_get_job_details += 1
                                    driver.refresh()
                                else:
                                    index += 1
                                    skipped_jobs += 1
                                    logger.info(
                                        f"parsed job {number_of_jobs_processed}/{total_number_of_jobs} "
                                        f"with {skipped_jobs} skipped jobs"
                                    )
                                    retry_attempt_to_get_job_details = 0
                            else:
                                timestamp = get_posted_date(driver)
                                if timestamp is False:
                                    if retry_attempt_to_get_job_details < retry_max_to_get_job_details:
                                        retry_attempt_to_get_job_details += 1
                                        driver.refresh()
                                    else:
                                        index+=1
                                        skipped_jobs+=1
                                        logger.info(
                                            f"parsed job {number_of_jobs_processed}/{total_number_of_jobs} "
                                            f"with {skipped_jobs} skipped jobs"
                                        )
                                        retry_attempt_to_get_job_details = 0
                                elif company_name not in COMPANIES_TO_SKIP:
                                    timestamp = timestamp.timestamp()
                                    exports_writer.writerow([
                                        job_id, job_title, company_name, timestamp,
                                        location, f"https://www.linkedin.com{job_link}", job_already_applied, easy_apply,
                                        job_closed
                                    ])
                                    exports.flush()
                                    number_of_jobs_processed += 1
                                    logger.info(
                                        f"parsed job {number_of_jobs_processed}/{total_number_of_jobs} for "
                                        f"{search_filter}"
                                    )
                                    index += 1
            search_filter_time2 = time.perf_counter()
            time_run[search_filter] = search_filter_time2 - search_filter_time1

        driver.quit()
        time2 = time.perf_counter()
        logger.info(f"run time = {get_time_string(time2 - time1)}")
        for key, value in time_run.items():
            logger.info(f" {key} run time = {get_time_string(value)}")
        os.remove(status_file_name)


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
