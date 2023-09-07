from django.core.management import BaseCommand

from jobs.models import Job, JobLocation, JobNote, Item


class Command(BaseCommand):
    
    def handle(self, *args, **options):
        jobs = Job.objects.all()
        the_jobs = {}
        index = 0
        number_of_jobs = len(jobs)
        for job in jobs:
            key = f"{job.job_title}-{job.organisation_name}-{job.date_posted}"
            if key in the_jobs:
                the_jobs[key]['location'].append(job)
            else:
                the_jobs[key] = {
                    "job": job,
                    "location": [job]
                }
            index += 1
            print(f"\rprocessed job {index}/{number_of_jobs}", end='')
        print()
        number_of_items = len(the_jobs.keys())
        index = 0
        the_jobs = list(the_jobs.values())
        for job in the_jobs:
            job_posting = job['job']
            for location in job['location']:
                JobLocation.objects.all().get_or_create(
                    job_posting=job['job'],
                    linkedin_id=location.linkedin_id,
                    location=location.location,
                    linkedin_link=location.linkedin_link
                )
                if location != job_posting:
                    try:
                        location_note = location.note
                        try:
                            job_note = job_posting.jobnote
                            job_note.note += f"\n{location_note}"
                            job_note.save()
                        except JobNote.DoesNotExist:
                            JobNote.objects.all().get_or_create(
                                note=location_note,
                                user_id=1,
                                job=job_posting
                            )
                    except JobNote.DoesNotExist:
                        pass
                    for list_item in location.item_set.all():
                        matching_list = job_posting.item_set.all().filter(list_id=list_item.list_id).first()
                        # print()
                        # print(list_item.list_name)
                        # job_post_names = ", ".join(job_posting.item_set.all().values_list('list__name', flat=True))
                        # print(job_post_names)
                        if matching_list is None:
                            Item.objects.all().get_or_create(job=job_posting, list=list_item.list)
                        # print()
                    location.delete()
            index += 1
            print(f"\rprocessed key job {index}/{number_of_items}", end='')