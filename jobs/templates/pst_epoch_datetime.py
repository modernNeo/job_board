import datetime

from dateutil.tz import tz


def pst_epoch_datetime(millisecond_epoch):
    return datetime.datetime.fromtimestamp(
        int(millisecond_epoch)//1000
    ).replace(
        microsecond=int(millisecond_epoch) % 1000*10
    ).astimezone(tz.gettz('Canada/Pacific'))
