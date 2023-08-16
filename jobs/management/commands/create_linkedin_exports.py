import csv
import datetime
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


def get_posted_date(driver):
    primary_description = driver.find_element(
        by=By.CLASS_NAME, value="jobs-unified-top-card__primary-description"
    )
    location_and_posted_date = primary_description.text.split(" · ")[1]
    dividing_index = len(location_and_posted_date)
    word_index = 0
    while word_index <= 3:
        dividing_index = location_and_posted_date[:dividing_index].rfind(" ")
        word_index += 1
    date_posted = location_and_posted_date[dividing_index:].strip()

    post_date = datetime.datetime.now(
        tz=tz.gettz('Canada/Pacific')
    ).replace(minute=0).replace(second=0).replace(microsecond=0)
    duration = int(date_posted[:date_posted.find(" ")])
    if 'month' in date_posted:
        post_date -= datetime.timedelta(days=(30 * duration))
        post_date = post_date.replace(hour=0)
    elif 'week' in date_posted:
        post_date -= datetime.timedelta(days=(7 * duration))
        post_date = post_date.replace(hour=0)
    elif 'day' in date_posted:
        post_date -= datetime.timedelta(days=duration)
        post_date = post_date.replace(hour=0)
    elif 'hour' in date_posted:
        post_date -= datetime.timedelta(hours=duration)
    return post_date


def get_job(driver):
    return [
        item for item in BeautifulSoup(driver.page_source, 'html.parser').findAll("li")
        if 'class' in item.attrs and 'jobs-search-results__list-item' in item.attrs['class']
    ]


class Command(BaseCommand):

    def handle(self, *args, **options):
        time1 = time.perf_counter()
        today = datetime.datetime.today().astimezone(tz.gettz('Canada/Pacific'))
        EXPERIENCE_LEVEL_FILTER = "f_E=2%2C3%2C4"
        FT_OR_CONTRACT_FILTER = "f_JT=F%2CC"
        FILTER_FOR_ALL_JOBS = f"{EXPERIENCE_LEVEL_FILTER}&{FT_OR_CONTRACT_FILTER}"
        REMOTE_FILTER = "f_WT=2"
        WFH_AND_REMOTE_FILTER = f"{REMOTE_FILTER}%2C3"
        JAVA_KEYWORD = "keywords=intermediate%20java%20developer"
        SOFTWARE_KEYWORD = "keywords=intermediate%20software%20developer"
        CANADA = "location=Canada"
        VANCOUVER = "location=Vancouver%2C%20British%20Columbia%2C%20Canada"

        opts = FirefoxOptions()
        # opts.add_argument("--headless")
        driver = webdriver.Firefox(options=opts)

        driver.get("https://www.linkedin.com/uas/login")
        driver.find_element(value='username').send_keys(settings.LINKEDIN_EMAIL)
        word = driver.find_element(value='password')
        word.send_keys(settings.LINKEDIN_PASSWORD)
        word.submit()
        time.sleep(6)
        exports = open(f'{today.strftime("%Y-%m-%d_%I-%M-%S_%p")}_linkedin_exports.csv', mode='w')
        exports_writer = csv.writer(exports, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        search_filters = [
            f"{FILTER_FOR_ALL_JOBS}&{CANADA}&{JAVA_KEYWORD}&{REMOTE_FILTER}",
            f"{FILTER_FOR_ALL_JOBS}&{CANADA}&{SOFTWARE_KEYWORD}&{REMOTE_FILTER}",
            f"{FILTER_FOR_ALL_JOBS}&{VANCOUVER}&{JAVA_KEYWORD}&{WFH_AND_REMOTE_FILTER}"
            f"{FILTER_FOR_ALL_JOBS}&{VANCOUVER}&{SOFTWARE_KEYWORD}&{WFH_AND_REMOTE_FILTER}"
        ]
        exports_writer.writerow(
            ["jobId", "jobTitle", "companyName", "postDate", "location", "jobUrl", "applied", "isEasyApply"]
        )
        input("clear to go ahead?")
        for search_filter in search_filters:
            more_jobs_to_search = True
            page = 0
            while more_jobs_to_search:
                url = f"https://www.linkedin.com/jobs/search/?{search_filter}&refresh=true&sortBy=DD"
                if page > 0:
                    url += f"&start={25 * page}"
                page += 1
                driver.get(url)

                time.sleep(5)
                jobs = None
                try:
                    jobs = driver.find_element(
                        by=By.CLASS_NAME, value='scaffold-layout__list-container'
                    ).find_elements(
                        by=By.XPATH, value=".//li[contains(@id, 'ember')]"
                    )
                except NoSuchElementException:
                    more_jobs_to_search = False
                if more_jobs_to_search and jobs is not None:
                    jobs_list = get_job(driver)
                    for index, job in enumerate(jobs):
                        job.click()
                        time.sleep(4)
                        try:
                            job_info_item = jobs_list[index].contents[1].contents[1].contents[1].contents[3]
                        except AttributeError:
                            driver.execute_script("arguments[0].scrollIntoView();", job)
                            time.sleep(4)
                            jobs_list = get_job(driver)
                            job_info_item = jobs_list[index].contents[1].contents[1].contents[1].contents[3]
                        job_title = job_info_item.contents[1].text.replace("\n", "").strip()
                        job_link = re.search(r"/jobs/view/\d*/", job_info_item.contents[1].contents[1].attrs["href"])[0]
                        job_id = int(re.findall(r'\d+', job_link)[0])
                        company_name = job_info_item.contents[3].text.replace("\n", "").strip()
                        location = job_info_item.contents[5].text.replace("\n", "").strip()

                        easy_apply = None
                        applied = True
                        try:
                            apply_button_text = driver.find_element(by=By.CLASS_NAME, value="jobs-apply-button").text
                            applied = apply_button_text not in ['Apply', "Easy Apply"]
                            easy_apply = apply_button_text == "Easy Apply"
                        except NoSuchElementException:
                            pass
                        exports_writer.writerow([
                                job_id, job_title, company_name, get_posted_date(driver).timestamp(),
                                location, f"https://www.linkedin.com{job_link}", applied, easy_apply
                            ])
                        exports.flush()

        driver.quit()
        time2 = time.perf_counter()
        total_seconds = time2 - time1
        print(f"number of seconds = {total_seconds}")
