import datetime
import logging
import os
import shutil
import sys

import pytz
from django.conf import settings

barrier_logging_level = logging.ERROR

date_timezone = pytz.timezone('US/Pacific')


class CSSSDebugStreamHandler(logging.StreamHandler):
    def emit(self, record):
        if record.levelno < barrier_logging_level:
            super().emit(record)


class PSTFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, tz=None):
        super(PSTFormatter, self).__init__(fmt, datefmt)
        self.tz = tz

    def formatTime(self, record, datefmt=None):  # noqa: N802
        dt = datetime.datetime.fromtimestamp(record.created, self.tz)
        if datefmt:
            return dt.strftime(datefmt)
        else:
            return str(dt)


REDIRECT_STD_STREAMS = True
date_formatting_in_log = '%Y-%m-%d %H:%M:%S'
date_formatting_in_filename = "%Y_%m_%d_%H_%M_%S"
modular_log_prefix = "cmd_"
sys_stream_formatting = PSTFormatter(
    '%(asctime)s = %(levelname)s = %(name)s = %(message)s', date_formatting_in_log, tz=date_timezone
)


class Loggers:
    logger_list_indices = {}
    django_settings_file_path_and_name = None
    sys_stream_error_log_file_absolute_path = None
    the_logger = None

    @classmethod
    def get_logger(cls):
        if cls.the_logger is None:
            cls.the_logger = cls._add_settings_filehandler()
        return cls.the_logger

    @classmethod
    def _add_settings_filehandler(cls):
        # this is mostly here just so that the settings in the setting.spy can persist to all the debug logs
        # without other fluff being added to them
        date = datetime.datetime.now(date_timezone).strftime(date_formatting_in_filename)
        django_settings_logger = logging.getLogger(settings.DJANGO_SETTINGS_LOG_HANDLER_NAME)

        if not os.path.exists(f"{settings.LOG_LOCATION}/{settings.DJANGO_SETTINGS_LOG_HANDLER_NAME}"):
            os.makedirs(f"{settings.LOG_LOCATION}/{settings.DJANGO_SETTINGS_LOG_HANDLER_NAME}")

        django_settings_logger.setLevel(logging.DEBUG)
        cls.django_settings_file_path_and_name = (
            f"{settings.LOG_LOCATION}/{settings.DJANGO_SETTINGS_LOG_HANDLER_NAME}/{date}.log"
        )

        django_settings_filehandler = logging.FileHandler(cls.django_settings_file_path_and_name)
        django_settings_filehandler.setLevel(logging.DEBUG)
        django_settings_filehandler.setFormatter(sys_stream_formatting)
        django_settings_logger.addHandler(django_settings_filehandler)

        django_settings_error_filehandler = logging.FileHandler(
            f"{settings.LOG_LOCATION}/{settings.DJANGO_SETTINGS_LOG_HANDLER_NAME}/{date}_error.log"
        )
        django_settings_error_filehandler.setLevel(barrier_logging_level)
        django_settings_error_filehandler.setFormatter(sys_stream_formatting)
        django_settings_logger.addHandler(django_settings_error_filehandler)

        if REDIRECT_STD_STREAMS:
            sys.stdout = sys.__stdout__
        django_settings_stdout_stream_handler = CSSSDebugStreamHandler(sys.stdout)
        django_settings_stdout_stream_handler.setFormatter(sys_stream_formatting)
        django_settings_stdout_stream_handler.setLevel(logging.DEBUG)
        django_settings_logger.addHandler(django_settings_stdout_stream_handler)
        if REDIRECT_STD_STREAMS:
            sys.stdout = LoggerWriter(django_settings_logger.info)

        if REDIRECT_STD_STREAMS:
            sys.stderr = sys.__stderr__
        django_settings_stderr_stream_handler = logging.StreamHandler(sys.stderr)
        django_settings_stderr_stream_handler.setFormatter(sys_stream_formatting)
        django_settings_stderr_stream_handler.setLevel(barrier_logging_level)
        django_settings_logger.addHandler(django_settings_stderr_stream_handler)
        if REDIRECT_STD_STREAMS:
            sys.stderr = LoggerWriter(django_settings_logger.error)

        return django_settings_logger


class LoggerWriter:
    def __init__(self, level):
        self.level = level

    def write(self, message):
        if message != '\n':
            self.level(message)

    def flush(self):
        pass
