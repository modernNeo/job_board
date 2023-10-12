from rest_framework import serializers, viewsets
from rest_framework.response import Response

from jobs.models import JobNote, Job


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
