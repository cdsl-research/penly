from machine import Pin, RTC
import network, urequests, utime
import ujson

def getTime():
    if wifi == '':
        execfile("autowifi.py")
    
    rtc = RTC()

    url_jst = "http://worldtimeapi.org/api/timezone/Asia/Tokyo" # see http://worldtimeapi.org/timezones

    retry_delay = 5000 # interval time of retry after a failed Web query
    response = urequests.get(url_jst)

    # parse JSON
    parsed = response.json()
    #parsed=ujson.loads(res) # in case string
    datetime_str = str(parsed["datetime"])
    year = int(datetime_str[0:4])
    month = int(datetime_str[5:7])
    day = int(datetime_str[8:10])
    hour = int(datetime_str[11:13])
    minute = int(datetime_str[14:16])
    second = int(datetime_str[17:19])
    subsecond = int(round(int(datetime_str[20:26]) / 10000))

    # update internal RTC
    rtc.datetime((year, month, day, 0, hour, minute, second, subsecond))

    # setup day of the week
    daysOfTheWeek = "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"
    tm = utime.localtime(utime.mktime(utime.localtime()))

    # generate formated date/time strings from internal RTC
    date_str = "{0:4d}/{1:02d}/{2:02d}".format(*rtc.datetime())
    time_str = "{4:02d}:{5:02d}:{6:02d}".format(*rtc.datetime())
    date_ok = date_str + " " + time_str
    return date_ok

def timerSet():
    if wifi == '':
        execfile("autowifi.py")
    rtc = RTC()

    url_jst = "http://worldtimeapi.org/api/timezone/Asia/Tokyo" # see http://worldtimeapi.org/timezones

    retry_delay = 5000 # interval time of retry after a failed Web query
    response = urequests.get(url_jst)

    # parse JSON
    parsed = response.json()
    #parsed=ujson.loads(res) # in case string
    datetime_str = str(parsed["datetime"])
    year = int(datetime_str[0:4])
    month = int(datetime_str[5:7])
    day = int(datetime_str[8:10])
    hour = int(datetime_str[11:13])
    minute = int(datetime_str[14:16])
    second = int(datetime_str[17:19])
    subsecond = int(round(int(datetime_str[20:26]) / 10000))

    # update internal RTC
    rtc.datetime((year, month, day, 0, hour, minute, second, subsecond))

    # setup day of the week
    daysOfTheWeek = "Sun","Mon", "Tue", "Wed", "Thu", "Fri", "Sat"
    tm = utime.localtime(utime.mktime(utime.localtime()))

    #print(tm[6]+1)
    youbi = tm[6] + 1

    send_date = [year,month,day,youbi,hour,minute,second]
    #print(send_date)

    return send_date
