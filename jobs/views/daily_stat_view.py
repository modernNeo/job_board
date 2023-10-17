from rest_framework import serializers, viewsets

from jobs.models import DailyStat


class DailyStatSerializer(serializers.ModelSerializer):

    date_added = serializers.SerializerMethodField("date_exported_from_linkedin")

    def date_exported_from_linkedin(self, daily_stat):
        date = daily_stat.date_added.pst
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
