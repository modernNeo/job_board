import json

from django.http import HttpResponse
from django.views import View

from jobs.models import Job
from jobs.views.get_job_postings import get_job_postings


class PageNumbers(View):

    def get(self, request):
        jobs = Job.objects.all().filter(id=None) if self.request.user.id is None else Job.objects.all()
        (
            paginated_jobs, number_of_easy_apply_below_mid_senior_job_postings,
            number_of_non_easy_apply_below_mid_senior_job_postings, number_of_easy_apply_above_associate_job_postings,
            number_of_non_easy_apply_above_associate_job_postings
        ) = get_job_postings(
            jobs, request.user.id, list_parameter=request.GET['list']
        )
        response = {
            'total_number_of_pages': paginated_jobs.num_pages,
            'number_of_easy_apply_below_mid_senior_job_postings': number_of_easy_apply_below_mid_senior_job_postings,
            'number_of_non_easy_apply_below_mid_senior_job_postings': number_of_non_easy_apply_below_mid_senior_job_postings,
            'number_of_easy_apply_above_associate_job_postings': number_of_easy_apply_above_associate_job_postings,
            'number_of_non_easy_apply_above_associate_job_postings': number_of_non_easy_apply_above_associate_job_postings
        }
        return HttpResponse(json.dumps(response))
