import csv
import datetime

from dateutil.tz import tz
from django.core.management import BaseCommand

from jobs.csv_header import MAPPING
from jobs.setup_logger import Loggers
from jobs.views.indeed_scraper import run_indeed_scraper
from jobs.views.linkedin_scraper import run_linkedin_scraper

logger = Loggers.get_logger()


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--linkedin',
            action='store_true',
            default=False
        )
        parser.add_argument(
            '--indeed',
            action='store_true',
            default=False
        )

    def handle(self, *args, **options):
        today = datetime.datetime.today().astimezone(tz.gettz('Canada/Pacific'))

        exports = open(f'exports/{today.strftime("%Y-%m-%d_%I-%M-%S_%p")}_exports.csv', mode='w')
        exports_writer = csv.writer(exports, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        exports_writer.writerow(
            list(MAPPING.keys())
        )
        exports.flush()
        if options['indeed']:
            run_indeed_scraper(exports_writer, exports)
        if options['linkedin']:
            run_linkedin_scraper(logger, exports_writer, exports)