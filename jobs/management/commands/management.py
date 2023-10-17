from django.core.management import BaseCommand

from jobs.models import JobLocation, JobLocationDatePosted


class Command(BaseCommand):

    def handle(self, *args, **options):
        job_locations = JobLocation.objects.all()
        number_of_job_locations = job_locations.count()
        for index, job_location in enumerate(job_locations):
            job_location.save()
            # JobLocationDatePosted(
            #     date_posted=job_location.get_pst_posted_date,
            #     job_location_posting=job_location).save()
            print(f"processed job location {index}/{number_of_job_locations}")
