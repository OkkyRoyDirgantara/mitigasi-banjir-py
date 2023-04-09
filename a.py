from datetime import datetime

import pytz

if __name__ == '__main__':
    tz_jakarta = pytz.timezone('Asia/Jakarta')
    dt = datetime.now(tz_jakarta)
    print(dt.hour)