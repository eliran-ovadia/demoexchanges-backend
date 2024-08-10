import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # can choose from: DEBUG, INFO, WARNING, ERROR, CRITICAL
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  #Define log format
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler() #log messages to the console
    ]
)

logger = logging.getLogger(__name__)