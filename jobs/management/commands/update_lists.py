from django.core.management import BaseCommand

from jobs.models import UserJobPosting, List, Item


class Command(BaseCommand):

    def handle(self, *args, **options):
        user_job_postings = UserJobPosting.objects.all()
        applied_list, new = List.objects.all().get_or_create(name="Applied", user_id=1)
        hidden_list, new = List.objects.all().get_or_create(name="Hidden", user_id=1)
        french_list, new = List.objects.all().get_or_create(name="French", user_id=1)
        job_closed_list, new = List.objects.all().get_or_create(name='Job Closed', user_id=1)
        for user_job_posting in user_job_postings:
            log = []
            if user_job_posting.applied:
                log.append("job saved to apply")
                Item.objects.all().get_or_create(list=applied_list, job=user_job_posting.job_posting)
            if user_job_posting.hide:
                log.append("job saved to hidden")
                Item.objects.all().get_or_create(list=hidden_list, job=user_job_posting.job_posting)
            if user_job_posting.note is None or len(user_job_posting.note.strip()) == 0:
                user_job_posting.delete()
            elif 'french' in user_job_posting.note.lower():
                Item.objects.all().get_or_create(list=french_list, job=user_job_posting.job_posting)
                user_job_posting.delete()
            elif user_job_posting.note.strip() == 'no longer accepting applicants':
                Item.objects.all().get_or_create(list=job_closed_list, job=user_job_posting.job_posting)
                user_job_posting.delete()