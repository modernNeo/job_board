from rest_framework import serializers, viewsets

from jobs.models import JobNote, ExperienceLevelString, ExperienceLevel, Job
from jobs.views.get_job_postings import get_job_postings


class JobSerializer(serializers.ModelSerializer):
    lists = serializers.CharField(read_only=True)
    """
    https://www.cdrf.co/3.9/rest_framework.viewsets/ModelViewSet.html
    """
    note = serializers.SerializerMethodField('user_has_note')

    date_posted = serializers.SerializerMethodField("latest_job_date_posted")

    experience_level = serializers.SerializerMethodField('job_experience_level')

    job_board = serializers.SerializerMethodField('posting_job_board')

    easy_apply = serializers.SerializerMethodField("has_easy_apply")

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

    def job_experience_level(self, job):
        locations = job.joblocation_set.all()
        experience = -1
        for location in locations:
            if location.experience_level is not None and location.experience_level > experience:
                experience = location.experience_level
        if experience == -1:
            return None
        return ExperienceLevelString[list(ExperienceLevel)[experience].name]

    def posting_job_board(self, job):
        return ", ".join(set([location.job_board for location in job.joblocation_set.all()]))

    def has_easy_apply(self, job):
        return job.has_easy_apply

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
