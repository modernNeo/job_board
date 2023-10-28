# Job Board

I found the capabilities of LinkedIn and Indeed very lacking, specifically when it comes to
 1. Their features when it comes to allowing a user to organize job postings
 2. A wierd bug I find where sometimes a Job is not shown in the search results
 3. The same job posted multiple times, ones for each location, resulting in about 2-3 pages of search results all for the same job [LinkedIn is the one actually guilty of this]
 4. When doing a search, there is no way to make pertinent notes about a job posting, so I don't forget if a job posting is bugs and therefore should not spend time on it repeatedly

Due to this, I decided to setup my own job board to keep track of all the jobs relevant to me across both LinkedIn and Indeed [And hopefully support https://www.jobbank.gc.ca/jobsearch/jobsearch in the near future]

Limitations:
 1. Jobs have to be scraped in the morning using the django command `python manage.py create_job_scrape_export` before the csv is fed to the website and then parsed with `python manage.py parse_jobs_exports`
 2. Indeed is behind Cloudflare Captcha, so when scraping from them, you need to supervise the script while doing other tasks.
 3. LinkedIn can only be scraped with your own credentials, as without them, the only information that can be gathered about a job posting is its title, company and an approximation of when it was posted.

