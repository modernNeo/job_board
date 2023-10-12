from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View

from jobs.models import ETLFile


class IndexPage(View):

    def get(self, request):
        from django.urls import get_resolver
        get_resolver().reverse_dict.keys()
        return render(request, 'jobs/index.html', {"user": request.user.username, })

    def post(self, request):
        linkedin_exports = request.FILES.get("linkedin_exports", None)
        if linkedin_exports is not None:
            linkedin_exports = (dict(request.FILES))['linkedin_exports']
            for linkedin_export in linkedin_exports:
                ETLFile(file=linkedin_export).save()
        return HttpResponseRedirect("/")