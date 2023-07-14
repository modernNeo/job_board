from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db.models import Q
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
        linkedin_export = request.FILES.get("linkedin_exports", None)
        if linkedin_export is not None:
            fs = FileSystemStorage()
            fs.save(f"{settings.CSV_ROOT}/{linkedin_export.name}", linkedin_export)
            ETLFile(file_path=f"{settings.CSV_ROOT}/{linkedin_export.name}").save()
        return HttpResponseRedirect("/")


class JobSerializer(serializers.ModelSerializer):
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
        return job_postings.order_by('organisation_name', 'job_title')


class UserJobPostingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserJobPosting
        fields = '__all__'


class UserJobPostingViewSet(viewsets.ModelViewSet):
    serializer_class = UserJobPostingSerializer
    queryset = UserJobPosting.objects.all()

    def get_queryset(self):
        if self.kwargs.get("pk", None) is not None:
            return UserJobPosting.objects.all().filter(job_posting__job_id=self.kwargs['pk'])
        else:
            return UserJobPosting.objects.all()

    def get_object(self):
        return UserJobPosting.objects.all().filter(job_posting__job_id=self.kwargs['pk']).first()

    def post(self, request, pk):
        posting = UserJobPosting.objects.all().filter(user=request.user, job_posting__job_id=pk).first()
        if posting is None:
            posting = UserJobPosting(user=request.user, job_posting=Job.objects.get(job_id=pk))
        if request.data.get("hide", None) is not None:
            posting.hide = request.data['hide']
        if request.data.get("applied", None) is not None:
            posting.applied = request.data["applied"]
        if request.data.get("note", None) is not None:
            posting.note = request.data['note']
        posting.save()
        return Response("ok")