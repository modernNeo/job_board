from django.urls import path, include
from rest_framework import routers

from jobs.views import IndexPage, JobViewSet, UserJobPostingViewSet, PageNumbers, ListSet, ItemSet

router = routers.DefaultRouter()
router.register(r'jobs', JobViewSet, basename="job")
router.register(r'user_settings', UserJobPostingViewSet, basename="userjobposting"),
router.register(r'lists', ListSet, basename="list"),
router.register(r'items', ItemSet, basename="item"),

urlpatterns = [
    path(r'api/', include((router.urls, 'jobs'), namespace="api")),
    path(r'page_numbers', PageNumbers.as_view(), name='page_numbers'),
    path("", IndexPage.as_view(), name="index"),
]
