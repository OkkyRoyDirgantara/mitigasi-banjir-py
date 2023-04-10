from datetime import datetime, time
import pytz

tz_jakarta = pytz.timezone('Asia/Jakarta')
now_jakarta = datetime.now(tz_jakarta)
# time_now = now_jakarta.time()
# replace with your time
time_now = time(hour=5, minute=0, second=0, tzinfo=tz_jakarta)
intHour = int(time_now.strftime("%H"))
intMinute = int(time_now.strftime("%M"))
print(intHour)
print(intMinute)
print(time_now)
