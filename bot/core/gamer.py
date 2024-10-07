import asyncio
import hashlib
import hmac
import math
from time import time
import traceback
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw import functions
from pyrogram.raw.functions.messages import RequestWebView
import pytz
from bot.utils.logger import logger
from bot.utils.proxy import Proxy
from bot.utils.headers import headers_example
from aiocfscrape import CloudflareScraper
from pydantic_settings import BaseSettings
from random import randint, uniform
from urllib.parse import unquote
from datetime import datetime

class InvalidStartBot(BaseException):
    ...

class Gamer:
    def __init__(self, tg_session:Client, settings: BaseSettings, proxy: Proxy | None = None, user_agent: str | None = None) -> None:
        self.tg_session = tg_session
        self.settings = settings

        self.name = "@" + str(tg_session.workdir).split("/")[-1] if tg_session.workdir else tg_session.name
        self.proxy = proxy
        self.user_agent = user_agent
        self.headers = {}

    async def start(self):
        logger.info(f"Account {self.name} | started")
        
        connector = self.proxy.get_connector() if self.proxy else None
        self.headers = headers_example.copy()
        self.headers["User-Agent"] = self.user_agent
        client = CloudflareScraper(headers=self.headers, connector=connector)

  
async def run_gamer(tg_session: tuple[Client, Proxy, str], settings) -> None:
    """
    Starts a Gamer instance and waits for a random time between 1-5 seconds before doing so.
    
    Args:
        tg_session (tuple[Client, Proxy, str]): A tuple containing a Client instance, a Proxy instance and a User-Agent string.
        settings (Settings): The settings to use for this Gamer instance.
    """
    tg_session, proxy, user_agent = tg_session
    gamer = Gamer(tg_session=tg_session, settings=settings, proxy=proxy, user_agent=user_agent)
    try:
        sleep = randint(1, 5)
        logger.info(f"Account {gamer.name} | ready in {sleep}s")
        await asyncio.sleep(sleep)
        await gamer.start()
    except Exception as e:
        logger.error(f"Account {gamer.name} | Error: {e}")