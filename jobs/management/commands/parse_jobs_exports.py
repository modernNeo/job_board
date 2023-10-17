import datetime
import os

from django.core.management import BaseCommand

from jobs.models import ETLFile, DailyStat, pstdatetime
from jobs.views.parse_csv_export import parse_csv_export
from django.conf import settings


class Command(BaseCommand):

    def handle(self, *args, **options):
        daily_stat = DailyStat(
            number_of_new_jobs=0, number_of_new_job_locations=0, number_of_existing_inbox_jobs_closed=0,
            number_of_new_inbox_jobs_closed=0, number_of_existing_inbox_jobs_applied=0,
            number_of_new_inbox_jobs_applied=0
        )

        get_etl_start = lambda file_path_with_time: datetime.datetime.strptime(file_path_with_time[-34:-12], "%Y-%m-%d_%I-%M-%S_%p")

        if settings.PROD_ENVIRONMENT:
            csv_files = ETLFile.objects.all()
            if len(csv_files) != 1:
                print(f"got an unexpected number of csv files [{len(csv_files)}]")
                return
            csv_file = csv_files[0]
            if os.path.exists(csv_file.file_path):
                etl_extraction_start_time = get_etl_start(csv_file.file_path)
                daily_stat.date_added = pstdatetime.create_pst_time_from_datetime(etl_extraction_start_time)
                daily_stat.earliest_date_for_new_job_location = pstdatetime.create_pst_time_from_datetime(etl_extraction_start_time)
                daily_stat.save()
                parse_csv_export(csv_file.file_path, daily_stat)
            csv_file.delete()
        else:
            etl_extraction_start_time = get_etl_start(settings.EXPORT_FILE)
            daily_stat.date_added = pstdatetime.create_pst_time_from_datetime(etl_extraction_start_time)
            daily_stat.earliest_date_for_new_job_location = pstdatetime.create_pst_time_from_datetime(etl_extraction_start_time)
            daily_stat.save()
            parse_csv_export(settings.EXPORT_FILE, daily_stat)
