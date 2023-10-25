from rest_framework import serializers, viewsets
from rest_framework.response import Response

from jobs.models import JobItem, pstdatetime, Job, List


class ItemSerializer(serializers.ModelSerializer):
    list_name = serializers.CharField(read_only=True)

    date_added = serializers.SerializerMethodField("pst_date_added")

    def pst_date_added(self, item):
        # needed this func cause apparently the automatic serialization doesn't respect
        # from_db_value in PSTDateTimeField
        date_added = item.date_added
        if item.date_added is None:
            return None
        if type(date_added) != pstdatetime:
            date_added = pstdatetime.from_utc_datetime(date_added)
        return date_added.pst

    class Meta:
        model = JobItem
        fields = '__all__'


class ItemSet(viewsets.ModelViewSet):
    serializer_class = ItemSerializer
    queryset = JobItem.objects.all()

    def create(self, request, *args, **kwargs):
        query = request.query_params
        item_obj = JobItem(list=List.objects.get(id=query['list_id']), job=Job.objects.get(id=query['job_id']))
        item_obj.save()
        serializer = self.get_serializer(item_obj)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        item = self.queryset.filter(id=int(kwargs['pk'])).first()
        if item is not None:
            item.delete()
        return Response("ok")

    def get_queryset(self):
        return self.queryset.filter(
            job_id=self.request.query_params['job_id']
        ) if 'job_id' in self.request.query_params else self.queryset
