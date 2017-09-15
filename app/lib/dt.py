'''app.dt'''
import pytz
from datetime import datetime, date, time, timedelta
local_tz = pytz.timezone('America/Edmonton')

#-------------------------------------------------------------------------------
def json_serial(obj):
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError ("Type not serializable")

#-------------------------------------------------------------------------------
def to_utc(obj=None, dt=None, d=None, t=None, to_str=False):
    if obj:
        return convert_obj(obj, to_tz=pytz.utc, to_str=to_str)
    else:
        return to_timezone(pytz.utc, dt=dt, d=d, t=t, to_str=to_str)

#-------------------------------------------------------------------------------
def to_local(obj=None, dt=None, d=None, t=None, to_str=False):
    if obj:
        return convert_obj(obj, to_tz=local_tz, to_str=to_str)
    else:
        return to_timezone(local_tz, dt=dt, d=d, t=t, to_str=to_str)

#-------------------------------------------------------------------------------
def to_timezone(tz, dt=None, d=None, t=None, to_str=False):
    if dt:
        dt = dt.replace(tzinfo=local_tz) if not dt.tzinfo else dt
        dt = dt.astimezone(tz)
        return dt.strftime(to_str) if to_str else dt
    elif d and t:
        dt_ = datetime.combine(d,t)
        dt_ = local_tz.localize(dt_).astimezone(tz)
        return dt_.strftime(to_str) if to_str else dt_
    elif d and not t:
        dt_ = datetime.combine(d, time(0,0)).replace(tzinfo=local_tz).astimezone(tz)
        return dt_.strftime(to_str) if to_str else dt_

#-------------------------------------------------------------------------------
def d_to_dt(date_):
    return datetime.combine(date_, time())

#-------------------------------------------------------------------------------
def convert_obj(obj, to_tz=None, to_str=False):
    '''Returns a datetime with given timezone. Will convert timezones for
    non-naive datetimes
    @obj: any data structure (dict, list, etc)
    '''

    if isinstance(obj, dict):
        for k, v in obj.iteritems():
            obj[k] = convert_obj(v, to_str=to_str, to_tz=to_tz)
        return obj
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            obj[idx] = convert_obj(item, to_str=to_str, to_tz=to_tz)
        return obj
    elif isinstance(obj, datetime):
        tz = to_tz if to_tz else local_tz
        obj = obj.replace(tzinfo=tz) if not obj.tzinfo else obj.astimezone(tz)
        return obj.strftime(to_str) if to_str else obj
    else:
        return obj

#-------------------------------------------------------------------------------
def ddmmyyyy_to_dt(ddmmyyyy):
    '''@date_str: etapestry native dd/mm/yyyy
    '''
    parts = ddmmyyyy.split('/')
    return datetime(int(parts[2]), int(parts[1]), int(parts[0]))

#-------------------------------------------------------------------------------
def ddmmyyyy_to_date(ddmmyyyy):
    '''@date_str: etapestry native dd/mm/yyyy
    '''
    parts = ddmmyyyy.split('/')
    return date(int(parts[2]), int(parts[1]), int(parts[0]))

#-------------------------------------------------------------------------------
def ddmmyyyy_to_local_dt(ddmmyyyy):
    '''@date_str: etapestry native dd/mm/yyyy
    '''
    parts = ddmmyyyy.split('/')
    return to_local(dt=datetime(int(parts[2]), int(parts[1]), int(parts[0])))

#-------------------------------------------------------------------------------
def dt_to_ddmmyyyy(dt):
    return dt.strftime('%d/%m/%Y')

#-------------------------------------------------------------------------------
def ddmmyyyy_to_mmddyyyy(ddmmyyyy):
    p = ddmmyyyy.split('/')
    return '%s/%s/%s' % (p[1],p[0],p[2])
