import datetime
import re
from enum import Enum

import pytz
from dateutil.tz import tzfile
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.db import models
from dateutil.tz import tz
from django.utils import timezone

TIME_ZONE = 'Canada/Pacific'
PACIFIC_TZ = tz.gettz(TIME_ZONE)
UTC_TZ = pytz.UTC


def create_pst_time(year, month, day, hour_24=0, minute=0, second=0):
    """
    Creates a PST timezone object with the given parameters

    Keyword Arguments
    year -- the year (YYYY)
    month -- the month (01-12)
    day -- the day (01-XX)
    hour_24 -- -the hour (0-23)
    minute -- the minute (0-59)
    second -- the second (0-59)

    Return
    datetime -- the PST timezone object
    """
    return datetime.datetime(
        year=year, month=month, day=day, hour=hour_24, minute=minute, second=second, tzinfo=PACIFIC_TZ
    )


def create_utc_time(year, month, day, hour_24=0, minute=0, second=0):
    """
    Creates a UTC timezone object with the given parameters

    Keyword Arguments
    year -- the year (YYYY)
    month -- the month (01-12)
    day -- the day (01-XX)
    hour_24 -- -the hour (0-23)
    minute -- the minute (0-59)
    second -- the second (0-59)

    Return
    datetime -- the UTC timezone object
    """
    return datetime.datetime.fromtimestamp(
        create_pst_time(
            year=year, month=month, day=day, hour_24=hour_24, minute=minute, second=second
        ).timestamp()
    ).astimezone(UTC_TZ)


def convert_pacific_time_to_utc(pacific_date):
    """
    Convert the given Pacific timezone object to a UTC timezone object

    Keyword Arguments
    pacific_date -- the given pacific timezone object to convert

    Return
    datetime -- the UTC timezone equivalent of the pacific_date
    """
    return datetime.datetime.fromtimestamp(pacific_date.timestamp()).astimezone(UTC_TZ)


def convert_utc_time_to_pacific(utc_datetime):
    """
    Convert the given UTC timezone object to a PST timezone object

    Keyword Arguments
    utc_datetime -- the given UTC timezone object to convert

    Return
    datetime -- the PST timezone equivalent of the utc_datetime
    """
    return utc_datetime.astimezone(PACIFIC_TZ)


def create_pst_time_from_datetime(datetime_obj):
    """
    Creates a PST timezone object using a datetime object

    Keyword Arguments
    datetime_obj -- the datetime with the day and time to use to create the PST timezone object

    Return
    datetime -- the PST timezone object
    """
    return datetime.datetime(
        year=datetime_obj.year, month=datetime_obj.month, day=datetime_obj.day, hour=datetime_obj.hour,
        minute=datetime_obj.minute, second=datetime_obj.second, tzinfo=PACIFIC_TZ
    )


class PSTDateTimeField(models.DateTimeField):

    def pre_save(self, model_instance, add):
        """
        Makes sure to convert the date to UTC time before saving if its in Canada/Pacific timezone
        """
        date = getattr(model_instance, self.attname)
        # date can be None cause of end date
        if type(date) == str and date.strip() == "":
            setattr(model_instance, self.attname, None)
        elif date == 'Actively recruiting':
            setattr(model_instance, self.attname, None)
        elif date is not None:
            if type(date) is str and re.match(r"\d{4}-\d{2}-\d{2}", date):
                year = int(date[:4])
                month = int(date[5:7])
                day = int(date[8:10])
                setattr(model_instance, self.attname, create_utc_time(year, month, day))
            elif date.tzinfo == tzfile('/usr/share/zoneinfo/Canada/Pacific'):
                setattr(model_instance, self.attname, convert_pacific_time_to_utc(date))
        return super(PSTDateTimeField, self).pre_save(model_instance, add)

    def from_db_value(self, value, expression, connection):
        """
        Converts the value from the DB from UTC time to PST time before returning to calling code
        """
        # date can be None cause of end date
        if value is None:
            return None
        return convert_utc_time_to_pacific(value)


# Create your models here.


class DailyStat(models.Model):
    date_added = PSTDateTimeField(
        default=timezone.now
    )
    earliest_date_for_new_job_location = PSTDateTimeField(
        default=timezone.now
    )
    number_of_new_jobs = models.IntegerField(
        default=None,
        null=True
    )
    number_of_new_job_locations = models.IntegerField(
        default=None,
        null=True
    )
    number_of_existing_inbox_jobs_closed = models.IntegerField(
        default=None,
        null=True
    )
    number_of_new_inbox_jobs_closed = models.IntegerField(
        default=None,
        null=True
    )
    number_of_existing_inbox_jobs_applied = models.IntegerField(
        default=None,
        null=True
    )
    number_of_new_inbox_jobs_applied = models.IntegerField(
        default=None,
        null=True
    )


class ExportRunTime(models.Model):
    daily_stat = models.ForeignKey(
        DailyStat, on_delete=models.CASCADE
    )
    export_type = models.CharField(
        max_length=500
    )
    run_time_seconds = models.PositiveBigIntegerField(

    )

    def get_time_string(self):
        hours, minutes = 0, 0
        if self.run_time_seconds >= 60:
            minutes = int(self.run_time_seconds / 60)
            if minutes >= 60:
                hours = int(int(minutes) / 60)
                minutes = minutes % 60
        seconds = int(self.run_time_seconds % 60)
        run_time_str = ""
        if hours > 0:
            if hours >= 10:
                run_time_str += f"{hours:{3}} "
            else:
                run_time_str += f"{hours:{2}} "
            run_time_str += "hours"
        if minutes > 0:
            if len(run_time_str) > 0:
                run_time_str += ","
            if seconds == 0 and hours > 0:
                run_time_str += " and "
            if minutes >= 10:
                run_time_str += f"{minutes:{3}} "
            else:
                run_time_str += f"{minutes:{2}} "
            run_time_str += "minutes"
        if seconds > 0:
            if len(run_time_str) > 0:
                run_time_str += ", and"
            if seconds >= 10:
                run_time_str += f"{seconds:{3}} "
            else:
                run_time_str += f"{seconds:{2}} "
            run_time_str += "seconds"
        if run_time_str == "":
            run_time_str = " 0 seconds"
        return run_time_str


class Job(models.Model):
    job_title = models.CharField(
        max_length=500
    )
    company_name = models.CharField(
        max_length=500
    )
    easy_apply = models.BooleanField(

    )

    @property
    def note(self):
        return self.jobnote.note if self.jobnote is not None else None

    def get_latest_parsed_date(self):
        job_locations = self.joblocation_set.all()
        latest_date_added = None
        if len(job_locations) > 0:
            latest_date_added = job_locations[0].get_latest_parsed_date()
            for job_location in job_locations:
                try:
                    if job_location.updated_more_recently(latest_date_added):
                        latest_date_added = job_location.get_latest_parsed_date()
                except Exception as e:
                    print(e)
        return latest_date_added

    @property
    def lists(self):
        lists = List.objects.all().filter(item__job_id=self.id)
        if len(lists) == 0:
            return ""
        else:
            return "<->" + " || ".join(list(lists.order_by('id').values_list('name', flat=True)))


class ExperienceLevel(Enum):
    Internship = 0
    Entry_level = 1
    Associate = 2
    Mid_Senior_level = 3
    Director = 4


class JobLocation(models.Model):
    job_posting = models.ForeignKey(
        Job, on_delete=models.CASCADE
    )
    linkedin_id = models.PositiveBigIntegerField(

    )
    location = models.CharField(
        max_length=500
    )
    linkedin_link = models.CharField(
        max_length=5000
    )
    date_posted = PSTDateTimeField(
        null=True,
        blank=True
    )

    experience_level = models.IntegerField(
        default=None,
        null=True
    )

    def updated_more_recently(self, date_to_compare_to):
        job_location_daily_stats = self.joblocationdailystat_set.all()
        if len(job_location_daily_stats) == 0:
            return False
        if date_to_compare_to is None:
            return True
        for job_location_daily_stat in job_location_daily_stats:
            if job_location_daily_stat.daily_stat.date_added > date_to_compare_to:
                return True
        return False

    def get_latest_parsed_date(self):
        job_location_daily_stats = self.joblocationdailystat_set.all()
        latest_date_added = None
        for job_location_daily_stat in job_location_daily_stats:
            if job_location_daily_stat.updated_more_recently(latest_date_added):
                latest_date_added = job_location_daily_stat.daily_stat.date_added
        return latest_date_added


class JobLocationDailyStat(models.Model):
    daily_stat = models.ForeignKey(
        DailyStat, on_delete=models.CASCADE
    )
    job_location = models.ForeignKey(
        JobLocation, on_delete=models.CASCADE
    )

    def updated_more_recently(self, date_to_compare_to):
        if self.daily_stat.date_added is None:
            return date_to_compare_to
        if date_to_compare_to is None:
            return self.daily_stat.date_added
        return self.daily_stat.date_added >= date_to_compare_to


class List(models.Model):
    name = models.CharField(
        max_length=500
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE
    )

    @property
    def number_of_jobs(self):
        return len(Item.objects.all().filter(list_id=self.id))


class Item(models.Model):
    list = models.ForeignKey(
        List, on_delete=models.CASCADE,
    )
    job = models.ForeignKey(
        Job, on_delete=models.CASCADE,
    )
    date_added = PSTDateTimeField(
        default=timezone.now,
        null=True
    )

    @property
    def list_name(self):
        return self.list.name


class JobNote(models.Model):
    note = models.CharField(
        max_length=500
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE
    )
    job = models.OneToOneField(
        Job, on_delete=models.CASCADE,
    )


class ETLFile(models.Model):
    file_path = models.CharField(
        max_length=10000
    )

    def __init__(self, *args, **kwargs):
        file = None
        if 'file' in kwargs:
            file = kwargs['file']
            del kwargs['file']
        super(ETLFile, self).__init__(*args, **kwargs)
        if file is not None:
            fs = FileSystemStorage()
            fs.save(f"{settings.CSV_ROOT}/{file.name}", file)
            self.file_path = f"{settings.CSV_ROOT}/{file.name}"

    def delete(self, *args, **kwargs):
        fs = FileSystemStorage()
        try:
            fs.delete(self.file_path)
        except Exception:
            pass
        super(ETLFile, self).delete(*args, **kwargs)
