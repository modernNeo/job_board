from django.urls import path, include
from rest_framework import routers

from jobs.views.daily_stat_view import DailyStatSet
from jobs.views.index import IndexPage
from jobs.views.item_view import ItemSet
from jobs.views.job_location_view import JobLocationSet
from jobs.views.job_note_view import JobNoteSet
from jobs.views.jobs_applied_numbers import JobsAppliedNumbers
from jobs.views.jobs_views import JobViewSet
from jobs.views.list_view import ListSet

router = routers.DefaultRouter()
router.register(r'jobs', JobViewSet, basename="job")
router.register(r'lists', ListSet, basename="list"),
router.register(r'items', ItemSet, basename="item"),
router.register(r'locations', JobLocationSet, basename="location"),
router.register(f'notes', JobNoteSet, basename='note')
router.register(f'daily_stats', DailyStatSet, basename='daily_stat')

urlpatterns = [
    path(r'api/', include((router.urls, 'jobs'), namespace="api")),
    path(r'applied_stats', JobsAppliedNumbers.as_view(), name='jobs_applied_numbers'),
    path("", IndexPage.as_view(), name="index"),
]
