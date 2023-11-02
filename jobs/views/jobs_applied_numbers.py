import json

from django.http import HttpResponse
from django.views import View

from jobs.models import JobLocationDatePostedItem


class JobsAppliedNumbers(View):

    def get(self, request):
        applied_jobs = JobLocationDatePostedItem.objects.all().filter(
            list__name='Applied', date_applied_or_closed__isnull=False
        ).order_by('-date_applied_or_closed')
        applied_stats = {}
        index = 0
        last_date = None
        number_of_dates = 0
        jobs_pk_list = []
        while number_of_dates < 3:
            applied_job = applied_jobs[index]
            index += 1
            if applied_job.date_applied_or_closed is not None:
                job_location_posting = applied_job.job_location_date_posted.job_location_posting
                job = job_location_posting.job_posting
                if job.id not in jobs_pk_list:
                    jobs_pk_list.append(job.id)
                    easy_apply = job.has_easy_apply # keeping this cause I feel like the below line will throw errors
                    # for Applied jobs that couldn't be migrated to new relationship between Job and Applied list
                    easy_apply = job_location_posting.easy_apply
                    date_str = applied_job.date_applied_or_closed.pst.strftime("%Y-%m-%d")
                    if last_date != date_str:
                        number_of_dates += 1
                        last_date = date_str
                    if date_str not in applied_stats:
                        applied_stats[date_str] = {
                            'easy_apply': 1 if easy_apply else 0,
                            'company_website_apply': 0 if easy_apply else 1
                        }
                    else:
                        applied_stats[date_str]['easy_apply' if easy_apply else 'company_website_apply'] += 1
        return HttpResponse(json.dumps(applied_stats))
