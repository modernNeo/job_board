import json

from django.core.paginator import Paginator
from django.db.models import Q, F
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.views import View
from rest_framework import serializers, viewsets
from rest_framework.response import Response

from jobs.models import Job, UserJobPosting, ETLFile, List, Item, JobNote


def get_job_postings(job_postings, user_id, list_parameter=None):
    user_job_posting_customizations = UserJobPosting.objects.all().filter(user_id=user_id)
    if list_parameter is None or list_parameter == "all":
        pass
    if list_parameter == "inbox":
        job_postings = job_postings.filter(
            Q(job_id__in=list(user_job_posting_customizations.values_list('job_posting__job_id', flat=True))) |
            Q(userjobposting__isnull=True)
        )
        job_postings = job_postings.exclude(item__list__name='Archived')
    if f"{list_parameter}".isdigit():
        job_postings = job_postings.filter(item__list_id=int(list_parameter), item__list__user_id=user_id)
    if list_parameter == 'archived':
        job_postings = job_postings.filter(
            Q(job_id__in=list(user_job_posting_customizations.values_list('job_posting__job_id', flat=True))) |
            # capturing any jobs that still use the Posting table
            (Q(userjobposting__isnull=True) & Q(item__isnull=True))
            # if a job has neither object
        )
    # elif params.get("hidden", False) == 'true':
    #     user_job_posting_customizations = user_job_posting_customizations.filter(hide=True)
    #     job_postings = job_postings.filter(
    #         Q(job_id__in=list(user_job_posting_customizations.values_list('job_posting__job_id', flat=True)))
    #     )
    # elif params.get("applied", False) == 'true':
    #     user_job_posting_customizations = user_job_posting_customizations.filter(applied=True)
    #     job_postings = job_postings.filter(
    #         Q(job_id__in=list(user_job_posting_customizations.values_list('job_posting__job_id', flat=True)))
    #     )
    # else:
    #     user_job_posting_customizations = user_job_posting_customizations.filter(hide=False).filter(applied=False)
    #     job_postings = job_postings.filter(
    #         Q(job_id__in=list(user_job_posting_customizations.values_list('job_posting__job_id', flat=True))) |
    #         Q(userjobposting__isnull=True)
    #
    #     )
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
        paginated_jobs, total_number_of_jobs = get_job_postings(jobs, request.user.id,
                                                                list_parameter=request.GET['list'])
        response = {
            'total_number_of_pages': paginated_jobs.num_pages,
            'total_number_of_jobs': total_number_of_jobs
        }
        return HttpResponse(json.dumps(response))


class JobSerializer(serializers.ModelSerializer):
    note = serializers.CharField(read_only=True)
    lists = serializers.CharField(read_only=True)

    class Meta:
        model = Job
        fields = '__all__'


class JobViewSet(viewsets.ModelViewSet):
    serializer_class = JobSerializer

    def get_object(self):
        return Job.objects.get(id=int(self.kwargs['pk']))

    def get_queryset(self):
        job_postings = Job.objects.all()
        if self.request.user.id is None:
            return job_postings.filter(job_id=None)
        if 'list' in self.request.query_params:
            postings = get_job_postings(job_postings, self.request.user.id,
                                        list_parameter=self.request.query_params['list'])
        else:
            postings = get_job_postings(job_postings, self.request.user.id)
        if 'page' in self.request.query_params:
            return postings[0].page(self.request.query_params['page']).object_list
        else:
            return postings[0].page(1).object_list


class UserJobPostingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserJobPosting
        fields = '__all__'


class UserJobPostingViewSet(viewsets.ModelViewSet):
    serializer_class = UserJobPostingSerializer
    queryset = UserJobPosting.objects.all()

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
        if request.data.get("archived", None) is not None:
            posting.archived = request.data['archived']
        posting.save()
        return Response("ok")


class ListSerializer(serializers.ModelSerializer):
    class Meta:
        model = List
        fields = '__all__'


class ListSet(viewsets.ModelViewSet):
    serializer_class = ListSerializer
    queryset = List.objects.all()

    def create(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        return super(ListSet, self).create(request, args, kwargs)

    def get_queryset(self):
        request = self.request
        lists = self.queryset
        if 'job_id' in request.query_params:
            lists = lists.filter(item__job_id=request.query_params['job_id'])
        return lists.filter(user_id=request.user.id)


class ItemSerializer(serializers.ModelSerializer):
    list_name = serializers.CharField(read_only=True)
    class Meta:
        model = Item
        fields = '__all__'


class ItemSet(viewsets.ModelViewSet):
    serializer_class = ItemSerializer
    queryset = Item.objects.all()

    def create(self, request, *args, **kwargs):
        list_id = request.query_params['list_id']
        job_id = request.query_params['job_id']
        item_obj, new = self.queryset.get_or_create(list_id=list_id, job_id=job_id)
        item_obj.save()
        serializer = self.get_serializer(item_obj)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        item = self.queryset.filter(id=int(kwargs['pk'])).first()
        if item is not None:
            item.delete()
        return Response("ok")

    def get_queryset(self):
        items = self.queryset
        if 'job_id' in self.request.query_params:
            items = items.filter(job_id=self.request.query_params['job_id'])
        return items


class JobNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobNote
        fields = '__all__'


class JobNoteSet(viewsets.ModelViewSet):
    serializer_class = JobNoteSerializer
    queryset = JobNote.objects.all()

    def create(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        return super(JobNoteSet, self).create(request, args, kwargs)

    def destroy(self, request, *args, **kwargs):
        job_note = self.queryset.filter(id=int(kwargs['pk'])).first()
        if job_note is not None:
            job_note.delete()
        return Response("ok")

    def get_queryset(self):
        job_note = self.queryset
        if 'job_id' in self.request.query_params:
            job_note = job_note.filter(job_id=self.request.query_params['job_id'])
        return job_note
