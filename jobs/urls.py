from django.urls import path, include
from rest_framework import routers

from jobs.views import IndexPage, JobViewSet, UserJobPostingViewSet

router = routers.DefaultRouter()
router.register(r'jobs', JobViewSet, basename="job")
router.register(r'user_settings', UserJobPostingViewSet, basename="userjobposting")

urlpatterns = [
    path(r'api/', include((router.urls, 'jobs'), namespace="api")),
    path("", IndexPage.as_view(), name="index"),
]
