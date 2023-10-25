from django.db.models import Q
from rest_framework import serializers, viewsets

from jobs.models import List


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
            lists = lists.filter(
                Q(jobitem__job_id=request.query_params['job_id']) |
                Q(
                    joblocationdateposteditem__job_location_date_posted__job_location_posting__job_posting=
                    request.query_params['job_id']
                )
            )
        return lists.filter(user_id=request.user.id)
