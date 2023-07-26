import datetime
import re

import pytz
from dateutil.tz import tzfile
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.db import models
from dateutil.tz import tz

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

class Job(models.Model):
    linkedin_id = models.PositiveBigIntegerField(

    )
    job_title = models.CharField(
        max_length=500
    )
    organisation_id = models.CharField(
        max_length=500
    )
    organisation_name = models.CharField(
        max_length=500
    )
    location = models.CharField(
        max_length=500
    )
    remote_work_allowed = models.BooleanField(
    )
    workplace_type = models.CharField(
        max_length=500
    )

    date_posted = PSTDateTimeField(
        null=True,
        blank=True
    )

    source_domain = models.CharField(
        max_length=500
    )
    easy_apply = models.BooleanField(

    )
    linkedin_link = models.CharField(
        max_length=5000
    )

    @property
    def note(self):
        return self.jobnote.note if self.jobnote is not None else None

    @property
    def lists(self):
        lists = List.objects.all().filter(item__job_id=self.id)
        if len(lists) == 0:
            return ""
        else:
            return "<->" + " || ".join(list(lists.order_by('id').values_list('name', flat=True)))


class List(models.Model):
    name = models.CharField(
        max_length=500
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE
    )


class Item(models.Model):
    list = models.ForeignKey(
        List, on_delete=models.CASCADE,
    )
    job = models.ForeignKey(
        Job, on_delete=models.CASCADE,
    )

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
