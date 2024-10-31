import logging

logging.basicConfig(
    level=logging.DEBUG,  # minimum severity to log
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  #Define log format
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()  # log messages to the console
    ]
)

logger = logging.getLogger(__name__)
