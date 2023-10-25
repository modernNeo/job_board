from django.core.management import BaseCommand

from jobs.models import JobItem, JobLocationDatePostedItem, Job


class Command(BaseCommand):

    def handle(self, *args, **options):
        all_job_items = JobItem.objects.all().filter(list__name__in=['Job Closed', 'Applied'])
        number_of_job_items = all_job_items.count()
        for index, job_item in enumerate(all_job_items):
            if job_item.job.company_name == 'Red Label Vacations':
                print(1)
            job_item_with_location_date_posted = (
                job_item.job.joblocation_set.all()[0].joblocationdateposted_set.all().count() > 0
            )
            if job_item_with_location_date_posted:
                JobLocationDatePostedItem(
                    list=job_item.list,
                    job_location_date_posted=job_item.job.joblocation_set.all()[0].joblocationdateposted_set.all()[0],
                    date_added=job_item.date_added
                ).save()
                job_item.delete()
                print(
                    f"moved job_item {index}/{number_of_job_items} with list name {job_item.list_name}"
                    f" to JobLocationDatePostedItem"
                )
            else:
                print(f"skipping job_item {index}/{number_of_job_items} with list name {job_item.list_name}")
