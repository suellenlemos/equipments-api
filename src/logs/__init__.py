import os
import sys

from dotenv import load_dotenv
from loguru import logger

from src.helpers import EnvVarsTranslater

load_dotenv()

logger.remove()


def get_handler():
    if EnvVarsTranslater.get_bool("IS_RUNNING_LOCAL"):
        return sys.stdout


logger.add(
    sink=get_handler(),
    level=os.getenv('LOGGER_LEVEL').upper(),
)
