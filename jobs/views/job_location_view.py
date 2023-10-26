from django.db.models import When, Case
from rest_framework import serializers, viewsets
from rest_framework.response import Response

from jobs.models import ExperienceLevel, JobLocation


class JobLocationSerializer(serializers.ModelSerializer):

    date_posted = serializers.SerializerMethodField("date_posted_to_linkedin")

    experience_level = serializers.SerializerMethodField('get_experience_level')

    applied_status = serializers.SerializerMethodField('get_applied_status')

    closed_status = serializers.SerializerMethodField('get_closed_status')

    applied_item_id = serializers.SerializerMethodField('get_applied_item_id')

    closed_item_id = serializers.SerializerMethodField('get_closed_item_id')

    latest_date_posted_obj_id = serializers.SerializerMethodField('get_latest_date_posted_obj_id')

    def date_posted_to_linkedin(self, job_location):
        date = job_location.get_latest_job_location_posted_date_pst()
        return date.strftime("%Y %b %d %I:%m:%S %p") if date is not None else None

    def get_experience_level(self, job_location):
        return ExperienceLevel.get_experience_string(job_location.experience_level)

    def get_applied_status(self, job_location):
        items = job_location.get_job_items()
        applied_items = [item for item in items if item.list_name == 'Applied']
        return len(applied_items) > 0

    def get_closed_status(self, job_location):
        items = job_location.get_job_items()
        applied_items = [item for item in items if item.list_name == 'Job Closed']
        return len(applied_items) > 0

    def get_applied_item_id(self, job_location):
        items = job_location.get_job_items()
        applied_items = [item for item in items if item.list_name == 'Applied']
        return applied_items[0].id if len(applied_items) > 0 else None

    def get_closed_item_id(self, job_location):
        items = job_location.get_job_items()
        applied_items = [item for item in items if item.list_name == 'Job Closed']
        return applied_items[0].id if len(applied_items) > 0 else None

    def get_latest_date_posted_obj_id(self, job_location):
        return job_location.get_latest_job_location_posted_date_obj().id \
            if job_location.get_latest_job_location_posted_date_obj() is not None else None

    class Meta:
        model = JobLocation
        fields = '__all__'


class JobLocationSet(viewsets.ModelViewSet):
    serializer_class = JobLocationSerializer
    queryset = JobLocation.objects.all()

    def update(self, request, *args, **kwargs):
        job_location = JobLocation.objects.all().filter(id=kwargs['pk']).first()
        if job_location is not None:
            job_location.easy_apply = not job_location.easy_apply
            job_location.save()
        return Response("ok")

    def get_queryset(self):
        locations = self.queryset
        pk_list = []
        if 'job_id' in self.request.query_params:
            locations = locations.filter(job_posting_id=self.request.query_params['job_id'])
        locations = locations.order_by('-joblocationdateposted__date_posted')
        for location in locations:
            if location.id not in pk_list:
                pk_list.append(location.id)
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(pk_list)])
        return self.queryset.filter(pk__in=pk_list).order_by(preserved)

    def destroy(self, request, *args, **kwargs):
        job_location = self.queryset.filter(id=int(kwargs['pk'])).first()
        if job_location is not None:
            job_location.delete()
        return Response("ok")

