import sys
from loguru import logger


logger.remove()
logger.add(
    sink=sys.stdout, 
    format=(
        "<b>BLUM</b> | <white>{time:HH:mm:ss DD.MM}</white>"
        " | <red>LINE:{line: <7}</red>"
        " | <level>{level: <8}</level>"
        " | <white><i>{message}</i></white>"
    ),
    colorize=True,
    level="DEBUG"
)

logger.add(
    sink="blum_bot.log",
    format=(
        "{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}.{function} | LINE:{line} | {message}"
    ),
    rotation="10 MB",
    retention="10 days",
    compression="zip",
    level="DEBUG",
    enqueue=True
)
logger = logger.opt(colors=True)
