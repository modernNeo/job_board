import json
import re
import time

from bs4 import BeautifulSoup

from jobs.csv_header import INDEED_KEY


def run_indeed_scraper(exports_writer, exports):
    """
    https://codebeautify.org/jsonviewer
    https://jsonlint.com/
    https://medium.com/@denny-saputro/python-scraping-company-email-from-id-indeed-com-5d34cff993b7
    """

    import undetected_chromedriver as uc

    brave_path = '/usr/bin/brave-browser'
    option = uc.ChromeOptions()
    option.binary_location = brave_path
    driver = uc.Chrome(options=option)

    SOFTWARE_KEYWORD = 'q=intermediate+software+developer'
    INTERMEDIATE_JAVA_KEYWORD = 'q=intermediate+java+developer'
    JAVA_KEYWORD = 'q=java+developer'

    CANADA = 'l=Canada'
    VANCOUVER = 'l=Vancouver%2C+BC'

    REMOTE_JOB = 'sc=0kf%3Aattr%28DSQF7%29%3B'
    search_queries = {
        f"{CANADA}&{SOFTWARE_KEYWORD}&{REMOTE_JOB}": "Indeed Canada Intermediate Software Developer",
        f"{CANADA}&{INTERMEDIATE_JAVA_KEYWORD}&{REMOTE_JOB}": "Indeed Canada Intermediate Java Developer",
        f"{CANADA}&{JAVA_KEYWORD}&{REMOTE_JOB}": "Indeed Canada Java Developer",
        f"{VANCOUVER}&{SOFTWARE_KEYWORD}": "Indeed Vancouver Intermediate Software Developer",
        f"{VANCOUVER}&{INTERMEDIATE_JAVA_KEYWORD}": "Indeed Vancouver Intermediate Developer",
        f"{VANCOUVER}&{JAVA_KEYWORD}": "Indeed Vancouver Java Developer",
    }

    firstUrl = True
    for url_filter, human_readable_string in search_queries.items():
        page = 0
        more_jobs_to_search = True
        while more_jobs_to_search:
            url = f'https://ca.indeed.com/jobs?{url_filter}&sort=date'
            if page > 0:
                url += f"&start={(page * 10)}"
            page += 1
            print(f"getting {human_readable_string} page {page}")
            driver.get(url)
            time.sleep(10)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            if firstUrl:
                input("ok to proceed?")
                firstUrl = False
            data_parsing = BeautifulSoup(driver.page_source, "html.parser")
            navigation_tags = [tag for tag in data_parsing.find_all() if tag.name == "nav"]
            paginate_buttons = navigation_tags[len(navigation_tags) - 1].contents
            more_jobs_to_search = (
                len(paginate_buttons) > 0 and paginate_buttons[len(paginate_buttons) - 1].text == ""
            )

            scripts = data_parsing.find("script", {"id": "mosaic-data"})

            pattern = re.compile(r"window.mosaic.providerData\[\"mosaic-provider-jobcards\"]=.*;")
            string = None
            for item in pattern.findall(scripts.get_text(), re.DOTALL):
                string = item

            string = re.sub('window.mosaic.providerData\["mosaic-provider-jobcards"]=|;', '', string)

            stud_obj = json.loads(string)

            for job_info in stud_obj["metaData"]["mosaicProviderJobCardsModel"]["results"]:
                jobkey = job_info['jobkey']
                job_title = job_info['displayTitle']
                company_name = job_info['truncatedCompany']
                timestamp = job_info['pubDate']
                location = job_info['formattedLocation']
                exports_writer.writerow([
                    jobkey, job_title, company_name, timestamp, None, location,
                    f"https://ca.indeed.com/viewjob?jk={jobkey}", None, job_info['indeedApplyEnabled'], None,
                    INDEED_KEY
                ])
                exports.flush()
    driver.quit()
