from django.core.management import BaseCommand

from jobs.models import JobLocation, ETLFile


class Command(BaseCommand):

    def handle(self, *args, **options):
        ETLFile.objects.all().delete()
        for job_location in JobLocation.objects.all():
            job_location.job_board_id_str = job_location.job_board_id
            job_location.save()
            print(1)