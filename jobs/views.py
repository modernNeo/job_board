import json
import pickle

from django.core.paginator import Paginator
from django.db.models import Q, F
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.views import View
from rest_framework import serializers, viewsets, status
from rest_framework.response import Response

from jobs.models import Job, UserJobPosting, ETLFile, List


def get_job_postings(params, job_postings, user_id):
    user_job_posting_customizations = UserJobPosting.objects.all().filter(user_id=user_id)
    if params.get("hidden", False) == 'true':
        user_job_posting_customizations = user_job_posting_customizations.filter(hide=True)
        job_postings = job_postings.filter(
            Q(job_id__in=list(user_job_posting_customizations.values_list('job_posting__job_id', flat=True)))
        )
    elif params.get("applied", False) == 'true':
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
    ordered_postings = job_postings.order_by(F('date_posted').desc(nulls_last=True), 'organisation_name', 'job_title')
    return Paginator(ordered_postings, 25), len(job_postings)


class IndexPage(View):

    def get(self, request):
        from django.urls import get_resolver
        get_resolver().reverse_dict.keys()
        return render(request, 'jobs/index.html', {"user": request.user.username, })

    def post(self, request):
        linkedin_exports = request.FILES.get("linkedin_exports", None)
        if linkedin_exports is not None:
            linkedin_exports = (dict(request.FILES))['linkedin_exports']
            for linkedin_export in linkedin_exports:
                ETLFile(file=linkedin_export).save()
        return HttpResponseRedirect("/")


class PageNumbers(View):

    def get(self, request):
        jobs = Job.objects.all().filter(job_id=None) if self.request.user.id is None else Job.objects.all()
        paginated_jobs, total_number_of_jobs = get_job_postings(request.GET, jobs, request.user.id)
        response = {
            'total_number_of_pages': paginated_jobs.num_pages,
            'total_number_of_jobs': total_number_of_jobs
        }
        return HttpResponse(json.dumps(response))


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
        if 'list' in self.request.query_params:
            list_id = self.request.query_params['list']
            list_id = None if list_id == 'undefined' else list_id
            list_obj = List.objects.all().filter(id=list_id).first()
            return Response(list_obj.joblistitem_set.all() if list_obj is not None else list_obj)
        else:
            return get_job_postings(self.request.query_params, job_postings, self.request.user.id)[0].page(
                self.request.query_params['page']).object_list
        # return get_job_postings(
        #     self.request.query_params, job_postings, self.request.user.id
        # )[0].page(self.request.query_params['page']).object_list

    # def list(self, request, *args, **kwargs):
    #     if 'list' in request.query_params:
    #         list_id = request.query_params['list']
    #         list_id = None if list_id == 'undefined' else list_id
    #         list_obj = JobList.objects.all().filter(id=list_id).first()
    #         return Response(list_obj.joblistitem_set.all() if list_obj is not None else list_obj)
    #     else:
    #         job_postings = Job.objects.all()
    #         if self.request.user.id is None:
    #             return job_postings.filter(job_id=None)
    #         postings = get_job_postings(request.GET, job_postings, request.user.id)
    #         postings = postings[0]
    #         postings = postings.page(self.request.query_params['page'])
    #         postings = postings.object_list
    #
    #         serializer = self.get_serializer(data=postings)
    #         serializer.is_valid(raise_exception=True)
    #         headers = self.get_success_headers(serializer.data)
    #         return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


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


class ListCRUDSerializer(serializers.ModelSerializer):
    class Meta:
        model = List
        fields = '__all__'


class ListCRUDSet(viewsets.ModelViewSet):
    serializer_class = ListCRUDSerializer
    queryset = List.objects.all()

    def create(self, request, *args, **kwargs):
        data = request.data
        data['user'] = request.user.id

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        # list_obj = JobList(user_id=request.user.id)
        # list_obj.name = request.data['name']
        # list_obj.save()
        # serializer = self.get_serializer(data=list_obj)
        # serializer.is_valid(raise_exception=True)
        # headers = self.get_success_headers(serializer.data)
        # return Response(json.dumps(list_obj, default=ListCRUDSerializer))

    # def list(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=self.queryset.filter(user_id=request.user.id))
    #     serializer.is_valid(raise_exception=True)
    #     headers = self.get_success_headers(serializer.data)
    #     return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)
    #     pass

    # def update(self, request, *args, **kwargs):
    #     pass
    #
    # def destroy(self, request, *args, **kwargs):
    #     pass
