from rest_framework import serializers, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

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


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 1000

    def get_paginated_response(self, data):
        return Response({
            'links': {
               'next': self.get_next_link(),
               'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'total_number_of_pages': self.page.paginator.num_pages,
            'results': data
        })



class JobViewSet(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    queryset = Job.objects.all()
    pagination_class = StandardResultsSetPagination

    def get_object(self):
        return Job.objects.get(id=int(self.kwargs['pk']))

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        search_title = self.request.query_params.get("search_title", None)
        search_id = self.request.query_params.get("search_id", None)
        search_specified = search_id is not None or search_title is not None
        if search_title is not None:
            queryset = queryset.filter(job_title__contains=search_title)
        if search_id is not None:
            queryset = queryset.filter(joblocation__job_board_id__contains=search_id)
        if 'list' in self.request.query_params:
            posting_info = get_job_postings(
                queryset, self.request.user.id,
                list_parameter=self.request.query_params['list'] if not search_specified else None
            )
        else:
            posting_info = get_job_postings(queryset, self.request.user.id)
        queryset = posting_info[0]

        page_queryset = self.paginate_queryset(queryset)
        if page_queryset is not None:
            serializer = self.get_serializer(page_queryset, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data.update({
                'number_of_easy_apply_below_mid_senior_job_postings': posting_info[1],
                'number_of_non_easy_apply_below_mid_senior_job_postings': posting_info[2],
                'number_of_easy_apply_above_associate_job_postings': posting_info[3],
                'number_of_non_easy_apply_above_associate_job_postings': posting_info[4]
            })
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)