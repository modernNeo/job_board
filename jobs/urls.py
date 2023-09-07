from django.urls import path, include
from rest_framework import routers

from jobs.views import IndexPage, JobViewSet, PageNumbers, ListSet, ItemSet, JobNoteSet, JobLocationSet

router = routers.DefaultRouter()
router.register(r'jobs', JobViewSet, basename="job")
router.register(r'lists', ListSet, basename="list"),
router.register(r'items', ItemSet, basename="item"),
router.register(r'locations', JobLocationSet, basename="location"),
router.register(f'notes', JobNoteSet, basename='note')

urlpatterns = [
    path(r'api/', include((router.urls, 'jobs'), namespace="api")),
    path(r'page_numbers', PageNumbers.as_view(), name='page_numbers'),
    path("", IndexPage.as_view(), name="index"),
]
