from django.db.models import Q, F
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from rest_framework import serializers, viewsets
from rest_framework.response import Response

from jobs.models import Job, UserJobPosting, ETLFile


class IndexPage(View):

    def get(self, request):
        return render(request, 'jobs/index.html', {"user": request.user.username})

    def post(self, request):
        linkedin_exports = request.FILES.get("linkedin_exports", None)
        if linkedin_exports is not None:
            linkedin_exports = (dict(request.FILES))['linkedin_exports']
            for linkedin_export in linkedin_exports:
                ETLFile(file=linkedin_export).save()
        return HttpResponseRedirect("/")


class JobSerializer(serializers.ModelSerializer):
    note = serializers.CharField(read_only=True)

    class Meta:
        model = Job
        fields = '__all__'


class JobViewSet(viewsets.ModelViewSet):
    serializer_class = JobSerializer

    def get_queryset(self):
        job_postings = Job.objects.all()
        if self.request.user.id is None:
            return job_postings.filter(job_id=None)
        user_job_posting_customizations = UserJobPosting.objects.all().filter(user_id=self.request.user.id)
        if self.request.query_params.get("hidden", False) == 'true':
            user_job_posting_customizations = user_job_posting_customizations.filter(hide=True)
            job_postings = job_postings.filter(
                Q(job_id__in=list(user_job_posting_customizations.values_list('job_posting__job_id', flat=True)))
            )
        elif self.request.query_params.get("applied", False) == 'true':
            user_job_posting_customizations = user_job_posting_customizations.filter(applied=True)
            job_postings = job_postings.filter(
                Q(job_id__in=list(user_job_posting_customizations.values_list('job_posting__job_id', flat=True)))
            )
        else:
            user_job_posting_customizations = user_job_posting_customizations.filter(hide=False).filter(applied=False)
            job_postings = job_postings.filter(
                Q(job_id__in=list(user_job_posting_customizations.values_list('job_posting__job_id', flat=True))) |
                Q(userjobposting__isnull=True)

            )
        return job_postings.order_by(F('date_posted').desc(nulls_last=True), 'organisation_name', 'job_title')

class UserJobPostingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserJobPosting
        fields = '__all__'


class UserJobPostingViewSet(viewsets.ModelViewSet):
    serializer_class = UserJobPostingSerializer
    queryset = UserJobPosting.objects.all()

    # def get_queryset(self):
    #     if self.kwargs.get("pk", None) is not None:
    #         return Job.objects.all().filter(id=self.kwargs['pk']).first().userjobposting_set.all()
    #     else:
    #         return UserJobPosting.objects.all()

    def get_object(self):
        return Job.objects.all().filter(id=self.kwargs['pk']).first().userjobposting_set.all().first()

    def post(self, request, pk):
        postings = Job.objects.all().filter(id=pk).first().userjobposting_set.all()
        posting = [posting for posting in postings if posting.user == request.user]
        if len(posting) == 0:
            posting = UserJobPosting(user=request.user, job_posting=Job.objects.get(id=pk))
        else:
            posting = posting[0]
        if request.data.get("hide", None) is not None:
            posting.hide = request.data['hide']
        if request.data.get("applied", None) is not None:
            posting.applied = request.data["applied"]
        if request.data.get("note", None) is not None:
            posting.note = request.data['note']
        posting.save()
        return Response("ok")