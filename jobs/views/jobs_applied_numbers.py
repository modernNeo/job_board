import json

from django.http import HttpResponse
from django.views import View

from jobs.models import Item


class JobsAppliedNumbers(View):

    def get(self, request):
        applied_jobs = Item.objects.all().filter(
            list__name='Applied', date_added__isnull=False
        ).order_by('-date_added')
        applied_stats = {}
        index = 0
        last_date = None
        number_of_dates = 0
        while number_of_dates < 3:
            applied_job = applied_jobs[index]
            index += 1
            if applied_job.date_added is not None:
                easy_apply = applied_job.job.has_easy_apply
                date_str = applied_job.date_added.strftime("%Y-%m-%d")
                if last_date != date_str:
                    number_of_dates += 1
                    last_date = date_str
                if date_str not in applied_stats:
                    applied_stats[date_str] = {
                        'easy_apply' : 1 if easy_apply else 0,
                        'company_website_apply' : 0 if easy_apply else 1
                    }
                else:
                    applied_stats[date_str]['easy_apply' if easy_apply else 'company_website_apply'] += 1
        return HttpResponse(json.dumps(applied_stats))
