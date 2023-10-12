from rest_framework import serializers, viewsets
from rest_framework.response import Response

from jobs.models import Item


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
