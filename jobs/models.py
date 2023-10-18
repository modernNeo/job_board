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


class pstdatetime(datetime.datetime):
    """
    Create a pstdatetime object representing current object
    pstdatetime.now()

    Converting datetime.datetime to pstdatetime
    if the numbers in the datetime.datetime object are already in pacific time
    pstdatetime.from_datetime_with_pst_time(datetime_object)

    if the numbers in the datetime.datetime object are in UTC time
    pstdatetime.from_utc_datetime(datetime_object)

    creating object from epoch time
    pstdatetime.from_epoch(datetime_object)
    """

    PACIFIC_TZ = tz.gettz('Canada/Pacific')
    UTC_TZ = pytz.UTC

    @property
    def pst(self):
        return self.astimezone(self.PACIFIC_TZ) if self.tzinfo == self.UTC_TZ else self

    @property
    def utc(self):
        return self if self.tzinfo == self.UTC_TZ else self.astimezone(self.UTC_TZ)

    @classmethod
    def from_utc_datetime(cls, date: datetime.datetime):
        return pstdatetime(
            date.year, month=date.month, day=date.day, hour=date.hour, minute=date.minute, second=date.second,
            microsecond=date.microsecond, tzinfo=cls.UTC_TZ
        )

    @classmethod
    def from_datetime_with_pst_time(cls, datetime_obj):
        """
        Creates a PST timezone object using a datetime object

        Keyword Arguments
        datetime_obj -- the datetime with the day and time to use to create the PST timezone object

        Return
        datetime -- the PST timezone object
        """
        return pstdatetime(
            year=datetime_obj.year, month=datetime_obj.month, day=datetime_obj.day, hour=datetime_obj.hour,
            minute=datetime_obj.minute, second=datetime_obj.second, tzinfo=cls.PACIFIC_TZ
        )

    @classmethod
    def from_epoch(cls, epoch_time: int):
        try:
            date = pstdatetime.fromtimestamp(epoch_time).astimezone(cls.UTC_TZ)
        except ValueError:
            date = pstdatetime.fromtimestamp(
                int(epoch_time)//1000
            ).replace(microsecond=int(epoch_time) % 1000 * 10).astimezone(cls.UTC_TZ)
        return date.pst

    @classmethod
    def create_pst_time(cls, year, month, day, hour_24=0, minute=0, second=0):
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
        return pstdatetime(
            year=year, month=month, day=day, hour=hour_24, minute=minute, second=second, tzinfo=cls.PACIFIC_TZ
        )

    @classmethod
    def create_utc_time(cls, year, month, day, hour_24=0, minute=0, second=0):
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
        return cls.create_pst_time(
                year=year, month=month, day=day, hour_24=hour_24, minute=minute, second=second
            ).utc


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
                setattr(model_instance, self.attname, pstdatetime.create_utc_time(year, month, day))
            elif date.tzinfo == tzfile('/usr/share/zoneinfo/Canada/Pacific'):
                setattr(model_instance, self.attname, date.utc)
            elif date.tzinfo is None:
                raise Exception("no timezone detected")
        return super(PSTDateTimeField, self).pre_save(model_instance, add)

    def from_db_value(self, value, expression, connection):
        """
        Converts the value from the DB from UTC time to PST time before returning to calling code
        """
        # date can be None cause of end date
        if value is None:
            return None
        return pstdatetime.from_utc_datetime(value).pst


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

    @property
    def note(self):
        return self.jobnote.note if self.jobnote is not None else None

    def get_latest_posted_date(self):
        job_locations = self.joblocation_set.all()
        latest_date_added = None
        if len(job_locations) > 0:
            latest_date_added = job_locations[0].get_latest_posted_date()
            for job_location in job_locations[1:]:
                if latest_date_added is None:
                    latest_date_added = job_location.get_latest_posted_date()
                elif job_location.get_latest_posted_date() is not None:
                    if job_location.get_latest_posted_date() > latest_date_added:
                        latest_date_added = job_location.get_latest_posted_date()
        return latest_date_added

    @property
    def has_easy_apply(self):
        easy_apply = False
        for location in self.joblocation_set.all():
            if location.easy_apply:
                easy_apply = True
        return easy_apply

    @property
    def lists(self):
        lists = List.objects.all().filter(item__job_id=self.id)
        if len(lists) == 0:
            return ""
        else:
            return "<->" + " || ".join(list(lists.order_by('id').values_list('name', flat=True)))

    def save(self, *args, **kwargs):
        duplicate_jobs = Job.objects.all().filter(
            job_title=self.job_title, company_name=self.company_name
        ).exclude(id=self.id)
        if len(duplicate_jobs) > 0:
            raise Exception(f"duplicate job {self.id} detected")
        super(Job, self).save(args, kwargs)


class ExperienceLevel:
    _experience_level_map = {
        "Internship": 0,
        "Entry level": 1,
        "Associate": 2,
        "Mid-Senior level": 3,
        "Director": 4,
        '': None
    }

    @classmethod
    def get_associate_number(cls):
        return cls._experience_level_map["Associate"]

    @classmethod
    def get_experience_number(cls, experience_level: str):
        return cls._experience_level_map[experience_level]

    @classmethod
    def get_experience_number_from_csv(cls, experience_level: str):
        if experience_level == '':
            return None
        return experience_level

    @classmethod
    def get_experience_string(cls, experience_level: int):
        if experience_level is None:
            return None
        experience_levels = list(cls._experience_level_map.keys())
        return experience_levels[int(experience_level)]


class JobLocation(models.Model):
    job_posting = models.ForeignKey(
        Job, on_delete=models.CASCADE
    )
    job_board_id = models.CharField(
        max_length=500,
        default=None,
        null=True,
    )
    location = models.CharField(
        max_length=500
    )
    job_board_link = models.CharField(
        max_length=5000
    )

    experience_level = models.IntegerField(
        default=None,
        null=True
    )

    job_board = models.CharField(
        max_length=500,
        default=None,
        null=True
    )
    easy_apply = models.BooleanField(
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

    def get_latest_posted_date(self):
        job_location__dates_posted = self.joblocationdateposted_set.all()
        date_posted = job_location__dates_posted[0].date_posted.pst
        for job_location__date_posted in job_location__dates_posted[1:]:
            if job_location__date_posted.date_posted.pst > date_posted:
                date_posted = job_location__date_posted.date_posted.pst
        return date_posted

    def save(self, *args, **kwargs):
        duplicate_job_locations = JobLocation.objects.all().filter(
            job_board_id=self.job_board_id, location=self.location, job_board_link=self.job_board_link,
            experience_level=self.experience_level, job_board=self.job_board, easy_apply=self.easy_apply,
            job_posting__job_title=self.job_posting.job_title, job_posting__company_name=self.job_posting.company_name
        ).exclude(id=self.id)
        if len(duplicate_job_locations) > 0:
            duplicate_ids = ", ".join([str(job_location.id) for job_location in duplicate_job_locations])
            raise Exception(f"current job location being saved {self.id} is a duplicate for job locations {duplicate_ids}")
        super(JobLocation, self).save(args, kwargs)


class JobLocationDatePosted(models.Model):
    job_location_posting = models.ForeignKey(
        JobLocation, on_delete=models.CASCADE
    )
    date_posted = PSTDateTimeField(
        null=True,
        blank=True
    )


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
