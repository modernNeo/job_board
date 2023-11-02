import re

from rest_framework import serializers, viewsets
from rest_framework.response import Response

from jobs.models import JobLocationDatePostedItem, pstdatetime, JobLocationDatePosted, List, JobLocation


class JobLocationDatePostedItemSerializer(serializers.ModelSerializer):
    list_name = serializers.CharField(read_only=True)

    date_applied_or_closed = serializers.SerializerMethodField("pst_date_applied_or_closed")

    def pst_date_applied_or_closed(self, job_location_date_posted_item):
        # needed this func cause apparently the automatic serialization doesn't respect
        # from_db_value in PSTDateTimeField
        date_applied_or_closed = job_location_date_posted_item.date_applied_or_closed
        if job_location_date_posted_item.date_applied_or_closed is None:
            return None
        if type(date_applied_or_closed) != pstdatetime:
            date_added = pstdatetime.from_utc_datetime(date_applied_or_closed)
        return date_applied_or_closed.pst

    date_created = serializers.SerializerMethodField("pst_date_created")

    def pst_date_created(self, job_location_date_posted_item):
        # needed this func cause apparently the automatic serialization doesn't respect
        # from_db_value in PSTDateTimeField
        date_created = job_location_date_posted_item.date_created
        if job_location_date_posted_item.date_created is None:
            return None
        if type(date_created) != pstdatetime:
            date_created = pstdatetime.from_utc_datetime(date_created)
        return date_created.pst

    class Meta:
        model = JobLocationDatePostedItem
        fields = '__all__'


class JobLocationDatePostedItemSet(viewsets.ModelViewSet):
    serializer_class = JobLocationDatePostedItemSerializer
    queryset = JobLocationDatePostedItem.objects.all()

    def create(self, request, *args, **kwargs):
        query = request.query_params
        legacy_job_location = re.match("location_id_", query['job_location_date_posted_id'])
        if legacy_job_location:
            job_location = JobLocation.objects.get(id=int(query['job_location_date_posted_id'][12:]))
            job_location_date_posted = JobLocationDatePosted(job_location_posting=job_location, date_posted=None)
            job_location_date_posted.save()
        else:
            job_location_date_posted = JobLocationDatePosted.objects.get(id=query['job_location_date_posted_id'])
        include_date_applied_or_closed = query['dateAppliedOrClosed'] == 'true'
        if include_date_applied_or_closed:
            date_applied_or_closed = pstdatetime.now().pst
        else:
            date_applied_or_closed = None
        item_obj = JobLocationDatePostedItem(
            list=List.objects.get(id=query['list_id']),
            job_location_date_posted=job_location_date_posted,
            date_applied_or_closed=date_applied_or_closed
        )
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
            job_location_date_posted__job_location_posting__job_posting_id=self.request.query_params['job_id']
        ) if 'job_id' in self.request.query_params else self.queryset
