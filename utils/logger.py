import logging
from datetime import datetime

now = datetime.now()
log_date = now.strftime('%Y-%m-%d')
log_bot_filename = f'utils\logfile\log_bot_{log_date}.log'

def log_app():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )

    logger = logging.getLogger(log_bot_filename)



