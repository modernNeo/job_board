from rest_framework import serializers, viewsets
from rest_framework.response import Response

from jobs.models import ExperienceLevel, ExperienceLevelString, JobLocation


class JobLocationSerializer(serializers.ModelSerializer):

    date_posted = serializers.SerializerMethodField("date_posted_to_linkedin")

    experience_level = serializers.SerializerMethodField('get_experience_level')

    def date_posted_to_linkedin(self, job_location):
        date = job_location.get_latest_posted_date()
        return date.strftime("%Y %b %d %I:%m:%S %p") if date is not None else None

    def get_experience_level(self, job_location):
        for experience_level in ExperienceLevel:
            if experience_level.value == job_location.experience_level:
                return ExperienceLevelString[experience_level.name]
        return None

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
        if 'job_id' in self.request.query_params:
            locations = locations.filter(job_posting_id=self.request.query_params['job_id'])
        return locations.order_by('-date_posted')

    def destroy(self, request, *args, **kwargs):
        job_location = self.queryset.filter(id=int(kwargs['pk'])).first()
        if job_location is not None:
            job_location.delete()
        return Response("ok")

