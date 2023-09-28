import json

from django.core.paginator import Paginator
from django.db.models import F
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.views import View
from rest_framework import serializers, viewsets
from rest_framework.response import Response

from jobs.models import Job, ETLFile, List, Item, JobNote, JobLocation, DailyStat, PSTDateTimeField, ExperienceLevel


def get_job_postings(job_postings, user_id, list_parameter=None):
    if list_parameter is None or list_parameter == "all":
        pass
    elif list_parameter == "inbox":
        job_postings = job_postings.exclude(item__list__name='Archived')
    elif list_parameter == 'archived':
        job_postings = job_postings.filter(item__list__name='Archived')

        # necessary to remove any jobs that have entries in any other non-Archived lists
        job_postings = job_postings.exclude(item__in=Item.objects.all().exclude(list__name="Archived"))
    elif f"{list_parameter}".isdigit():
        job_postings = job_postings.filter(item__list_id=int(list_parameter), item__list__user_id=user_id)
    ordered_postings = job_postings.order_by(
        '-easy_apply', F('joblocation__experience_level').desc(nulls_last=True),
        F('joblocation__date_posted').desc(nulls_last=True), 'company_name', 'job_title', 'id'
    ).distinct()
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
        jobs = Job.objects.all().filter(id=None) if self.request.user.id is None else Job.objects.all()
        paginated_jobs, total_number_of_jobs = get_job_postings(jobs, request.user.id,
                                                                list_parameter=request.GET['list'])
        response = {
            'total_number_of_pages': paginated_jobs.num_pages,
            'total_number_of_jobs': total_number_of_jobs
        }
        return HttpResponse(json.dumps(response))


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
                easy_apply = applied_job.job.easy_apply
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


class JobSerializer(serializers.ModelSerializer):
    lists = serializers.CharField(read_only=True)
    """
    https://www.cdrf.co/3.9/rest_framework.viewsets/ModelViewSet.html
    """
    note = serializers.SerializerMethodField('user_has_note')

    date_posted = serializers.SerializerMethodField("latest_job_date_posted")

    @property
    def user_id_for_request(self):
        request = self.context.get('request', None)
        return request.user.id if request else None

    def user_has_note(self, job):
        note = JobNote.objects.all().filter(job_id=job.id, user_id=self.user_id_for_request).first()
        return note.note if note is not None else note

    def latest_job_date_posted(self, job):
        date = job.get_latest_parsed_date()
        return date.strftime("%Y %b %d %I:%m:%S %p") if date is not None else None

    class Meta:
        model = Job
        fields = '__all__'


class JobViewSet(viewsets.ModelViewSet):
    serializer_class = JobSerializer

    def get_object(self):
        return Job.objects.get(id=int(self.kwargs['pk']))

    # def list(self, request, *args, **kwargs):
    #     queryset = Job.objects.all()
    #
    #     page = self.paginate_queryset(queryset)
    #     if page is not None:
    #         serializer = self.get_serializer(page, many=True, user_id=self.request.user.id)
    #         return self.get_paginated_response(serializer.data)
    #
    #     serializer = self.get_serializer(queryset, many=True)
    #     return Response(serializer.data)

    def get_queryset(self):
        job_postings = Job.objects.all()
        if self.request.user.id is None:
            return job_postings.filter(id=None)
        if 'list' in self.request.query_params:
            postings = get_job_postings(job_postings, self.request.user.id,
                                        list_parameter=self.request.query_params['list'])
        else:
            postings = get_job_postings(job_postings, self.request.user.id)
        if 'page' in self.request.query_params:
            return postings[0].page(self.request.query_params['page']).object_list
        else:
            return postings[0].page(1).object_list


class ListSerializer(serializers.ModelSerializer):
    number_of_jobs = serializers.CharField(read_only=True)

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

    date_added = serializers.SerializerMethodField("pst_date_added")

    def pst_date_added(self, item):
        # needed this func cause apparently the automatic serialization doesn't respect
        # from_db_value in PSTDateTimeField
        return item.date_added

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


class JobLocationSerializer(serializers.ModelSerializer):

    date_posted = serializers.SerializerMethodField("date_posted_to_linkedin")

    experience_level = serializers.SerializerMethodField('get_experience_level')

    def date_posted_to_linkedin(self, job_location):
        date = job_location.date_posted
        return date.strftime("%Y %b %d %I:%m:%S %p") if date is not None else None

    def get_experience_level(self, job_location):
        for experience_level in ExperienceLevel:
            if experience_level.value == job_location.experience_level:
                return experience_level.name
        return None

    class Meta:
        model = JobLocation
        fields = '__all__'


class JobLocationSet(viewsets.ModelViewSet):
    serializer_class = JobLocationSerializer
    queryset = JobLocation.objects.all()

    def get_queryset(self):
        locations = self.queryset
        if 'job_id' in self.request.query_params:
            locations = locations.filter(job_posting_id=self.request.query_params['job_id'])
        return locations


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
        job_note = self.queryset.filter(job_id=int(kwargs['pk'])).first()
        if job_note is not None:
            job_note.delete()
        return Response("ok")

    def update(self, request, *args, **kwargs):
        job = Job.objects.all().filter(id=kwargs['pk']).first()
        if job is not None:
            note_obj = job.jobnote
            note_obj.note = request.data['note']
            note_obj.save()
        return Response("ok")

    def get_queryset(self):
        job_note = self.queryset
        if 'pk' in self.kwargs:
            job_note = job_note.filter(job_id=self.kwargs['pk'])
        return job_note


class DailyStatSerializer(serializers.ModelSerializer):

    date_added = serializers.SerializerMethodField("date_exported_from_linkedin")

    def date_exported_from_linkedin(self, daily_stat):
        date = daily_stat.date_added
        return date.strftime("%Y %b %d %I:%m:%S %p") if date is not None else None

    class Meta:
        model = DailyStat
        fields = '__all__'


class DailyStatSet(viewsets.ModelViewSet):
    serializer_class = DailyStatSerializer
    queryset = DailyStat.objects.all()

    def get_queryset(self):
        daily_stat = self.queryset.order_by('-date_added')
        if 'pk' in self.kwargs:
            daily_stat = daily_stat.filter(job_id=self.kwargs['pk'])
        return daily_stat
