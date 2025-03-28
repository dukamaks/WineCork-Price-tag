import sys
from loguru import logger as logging


logging.remove()
logging.add(sink=sys.stdout, format="<white>{time:HH:mm:ss}</white>"
                                   " | <level>{level: <8}</level>"
                                   " - <white><b>{message}</b></white>")
logging = logging.opt(colors=True)
