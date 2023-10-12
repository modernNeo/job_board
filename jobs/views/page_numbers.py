import json

from django.http import HttpResponse
from django.views import View

from jobs.models import Job
from jobs.views.get_job_postings import get_job_postings


class PageNumbers(View):

    def get(self, request):
        jobs = Job.objects.all().filter(id=None) if self.request.user.id is None else Job.objects.all()
        paginated_jobs, total_number_of_easy_apply_jobs, total_number_of_jobs = get_job_postings(
            jobs, request.user.id, list_parameter=request.GET['list']
        )
        response = {
            'total_number_of_pages': paginated_jobs.num_pages,
            'total_number_of_easy_apply_jobs': total_number_of_easy_apply_jobs,
            'total_number_of_jobs': total_number_of_jobs
        }
        return HttpResponse(json.dumps(response))
