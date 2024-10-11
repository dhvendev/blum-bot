import asyncio
from datetime import datetime
from random import randint, uniform
from time import time
from urllib.parse import unquote
from pyrogram import Client
from bot.utils.proxy import Proxy
from bot.utils.headers import headers_example
from pydantic_settings import BaseSettings
from bot.utils.logger import logger
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw.functions.messages import RequestWebView, StartBot
from aiocfscrape import CloudflareScraper

class InvalidStartTgApp(BaseException):
    ...

class InvalidLogin(BaseException):
    ...

class StartGameError(BaseException):
    ...

class ClaimRewardError(BaseException):
    ...

class StartFarmingError(BaseException):
    ...

class ClaimFarmingError(BaseException):
    ...

class DailyRewardError(BaseException):
    ...


class Blum:
    def __init__(self, tg_session: Client,
                settings: BaseSettings,
                proxy: Proxy | None = None,
                user_agent: str | None = None):
        
        self.tg_session = tg_session
        self.settings = settings

        self.name = "@" + str(tg_session.workdir).split("/")[-1] if tg_session.workdir else tg_session.name
        self.proxy = proxy

        self.headers = headers_example.copy()
        self.headers["User-Agent"] = user_agent

        self.token_live_time = randint(3500, 3600)
        self.jwt_token_create_time = 0
        self.jwt_live_time = randint(850, 900)
        self.access_token_created_time = 0

        self.logged = False


        self.auth_token = None
        self.access_token = None
        self.refresh_token = None
        self.user_auth_dict = None

        self.user_id = ""
        self.first_name = ""
        self.last_name = ""

        self.passes = 0
        self.available_balance = ""
        self.farming_end_time = 0

        self.__name_tg_bot = 'BlumCryptoBot'
        self.referal_param = settings.REF


    async def night_sleep_check(self):
        if bool(self.settings.NIGHT_SLEEP):
            time_now = datetime.now()

            # Start and end of the day
            sleep_start = time_now.replace(hour=0, minute=0, second=0, microsecond=0)  # 00:00 ночи
            sleep_end = time_now.replace(hour=8, minute=0, second=0, microsecond=0)    # 08:00 утра

            if time_now >= sleep_start and time_now <= sleep_end:
                time_to_sleep = (sleep_end - time_now).total_seconds()
                wake_up_time = time_to_sleep + randint(0, 3600)

                logger.info(f"{self.name} | Sleep until {sleep_end.strftime('%H:%M')}")
                await asyncio.sleep(wake_up_time)

            logger.info(f"{self.name} | Sleep cancelled | Now start the game")


    async def tg_app_start(self):
        try:
            if not self.tg_session.is_connected:
                await self.tg_session.connect()
            async for message in self.tg_session.get_chat_history(self.__name_tg_bot):
                if message.text and message.text.startswith('/start'):
                    logger.info('Command /start found.')
                    bot_peer = await self.tg_session.resolve_peer(self.__name_tg_bot)
                    break
            else:
                logger.info('Command /start not found. Send new command with referral parameter.')
                bot_peer = await self.tg_session.resolve_peer(self.__name_tg_bot)
                await self.tg_session.invoke(
                    StartBot(
                        bot=bot_peer,
                        peer=bot_peer,
                        start_param=self.referal_param,
                        random_id=randint(1, 9999999),
                    )
                )
                logger.info('Command /start sent successfully.')
        except (Unauthorized, UserDeactivated, AuthKeyUnregistered) as e:
            logger.error(f'Error start tg app: {e}')
            raise InvalidStartTgApp(e)


    async def login(self, session: CloudflareScraper):
        if not self.auth_token:
            raise InvalidLogin("Auth token not found")
        payload = { 
            "query": self.auth_token,
        }
        async with session.post("https://user-domain.blum.codes/api/v1/auth/provider/PROVIDER_TELEGRAM_MINI_APP", headers=self.headers, json=payload) as res:
            res.raise_for_status()
            user_data = await res.json()
            token = user_data.get('token', None)
            if not token:
                raise InvalidLogin("AccessToken not found")
            self.access_token = token.get('access', None)
            self.refresh_token = token.get('refresh', None)
            self.user_auth_dict = token.get('user', None)
            if not self.access_token or not self.refresh_token:
                raise InvalidLogin("AccessToken or RefreshToken not found")
            if not self.user_auth_dict:
                raise InvalidLogin("UserAuthDict not found")
            self.headers['Authorization'] = f"Bearer {self.access_token}"


    async def refresh_jwt_token(self, session: CloudflareScraper):
        current_time = time()
        if current_time - self.jwt_token_create_time >= self.jwt_live_time:
            if self.logged:
                logger.info(f"{self.name} | Access token expired, refreshing token.")
                await self.get_tg_web_data()
                await self.login(session)
                self.jwt_token_create_time = current_time  # Update create time after refresh
                self.jwt_live_time = randint(850, 900)    # Reset JWT live time


    async def refresh_access_token(self, session: CloudflareScraper) -> bool:
        current_time = time()
        if current_time - self.access_token_created_time >= self.token_live_time:
            await self.get_tg_web_data()
            await self.login(session)
            self.access_token_created_time = current_time  # Update token created time
            self.token_live_time = randint(3500, 3600)    # Reset token live time


    async def get_tg_web_data(self):
        peer = await self.tg_session.resolve_peer('BlumCryptoBot')
        web_view = await self.tg_session.invoke(RequestWebView(
            peer=peer,
            bot=peer,
            platform='android',
            from_bot_menu=False,
            url="https://telegram.blum.codes",
            start_param=self.referal_param
        ))
        auth_url = web_view.url
        print(auth_url)
        tg_web_data = unquote(
            string=unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])
        )
        self.user_id = tg_web_data.split('"id":')[1].split(',"first_name"')[0]
        self.first_name = tg_web_data.split('"first_name":"')[1].split('","last_name"')[0]
        self.last_name = tg_web_data.split('"last_name":"')[1].split('","username"')[0]
        if self.tg_session.is_connected:
            await self.tg_session.disconnect()
        self.headers['Tl-Init-Data'] = tg_web_data
        self.auth_token = tg_web_data
        return tg_web_data


    async def check_balance(self, session: CloudflareScraper) -> bool:
        async with session.get("https://game-domain.blum.codes/api/v1/user/balance", headers=self.headers) as res:
            if res.status != 200:
                logger.warning(f"{self.name} | <yellow>Get user balance failed: {res.status})</yellow>")
                return False
            data = await res.json()
            self.passes = data.get('playPasses', 0)
            self.available_balance = data.get('availableBalance', "")
            self.farming_end_time = data.get('farming', {}).get('endTime', 0)
            logger.info(f"{self.name} | Balance: <light-yellow>{self.available_balance}</light-yellow> |"
                        f"Passes: <light-yellow>{self.passes}</light-yellow>")
            return True


    async def start_game(self, session: CloudflareScraper) -> str | None:
        async with session.post("https://game-domain.blum.codes/api/v1/game/play", headers=self.headers) as res:
            if res.status != 200:
                logger.warning(f"{self.name} | <yellow>Start game failed: {res.status})</yellow>")
                return False
            data = await res.json()
            game_id = data.get('gameId', None)
            if not game_id:
                logger.warning(f"{self.name} | <yellow>Start game failed: GameId not found</yellow>")
                raise StartGameError("GameId not found")
            logger.info(f"{self.name} | <light-green>Start game: </light-green><cyan>{game_id}</cyan>")
            return game_id


    async def claim_reward(self, session: CloudflareScraper, game_id: str, points: int) -> bool:
        payload = {
            "gameId": game_id,
            "points": points
        }
        async with session.post(f"https://game-domain.blum.codes/api/v1/game/claim", headers=self.headers, json=payload) as res:
            if res.status != 200:
                logger.warning(f"{self.name} | <yellow>Claim reward failed: {res.status})</yellow>")
                raise ClaimRewardError(f"Claim reward failed gameId: {game_id} status: {res.status}")
            logger.info(f"{self.name} | <light-green>Claim reward: </light-green><cyan>{points}</cyan> with <light-blue>{game_id}</light-blue>")
            return True


    async def start_farming(self, session: CloudflareScraper) -> bool:
        """
        Start farming daily.

        This method sends a POST request to start farming.
        If the request is successful, it will update the account's farming end time.

        Returns:
            bool: True if the start is successful, False otherwise.
        """
        try:
            async with session.post("https://game-domain.blum.codes/api/v1/farming/start", headers=self.headers) as res:
                if res.status != 200:
                    raise StartFarmingError(f"Start farming failed: {res.status}")
                logger.info(f"{self.name} | Attempting to start farming")
                data = await res.json()
                self.farming_end_time = data.get('endTime')
                return True
        except StartFarmingError as e:
            logger.warning(f"{self.name} | <yellow>Start farming failed: {e})</yellow>")
        except Exception as e:
            logger.warning(f"{self.name} | <yellow>Start farming failed: {e})</yellow>")
        return False

    async def claim_farming(self, session: CloudflareScraper) -> bool:
        """
        Claim farming reward.

        This method sends a POST request to claim the farming reward.
        If the request is successful, it will update the account balance
        and passes.

        Returns:
            bool: True if the claim is successful, False otherwise.
        """
        try:
            current_time = time()
            if self.farming_end_time < current_time:
                logger.info(f"{self.name} | Farming not ready")
                return False
            logger.info(f"{self.name} | Attempting to claim farming")
            await asyncio.sleep(uniform(0.1, 1.0))
            async with session.post("https://game-domain.blum.codes/api/v1/farming/claim", headers=self.headers) as res:
                if res.status == 425:
                    raise ClaimFarmingError("Claim farming failed (it's already claimed)")
                if res.status == 200:
                    data = await res.json()
                    self.available_balance = data.get('availableBalance', "")
                    self.passes = data.get('playPasses', 0)
                    logger.success(f"{self.name} | <light-green>Claim daily farming success </light-green>")
                    return True
        except ClaimFarmingError as e:
            logger.warning(f"{self.name} | <yellow>Claim farming failed: {e})</yellow>")
        except Exception as e:
            logger.warning(f"{self.name} | <yellow>Claim farming failed: {e})</yellow>")
        return False


    async def daily_reward(self, session: CloudflareScraper):
        payload = {
            "query": -180,
        }
        async with session.get("https://game-domain.blum.codes/api/v1/daily-reward", headers=self.headers, json=payload) as res:
            if res.status == 404:
                logger.warning(f"{self.name} | <yellow>Daily reward already claimed</yellow>")
                return False
            if res.status != 200:
                return False
        async with session.post("https://game-domain.blum.codes/api/v1/daily-reward", headers=self.headers, json=payload) as res:
            if res.status != 200:
                return False
            if res.status == 200:
                logger.info(f"{self.name} | <light-green>Daily reward claimed</light-green>")
                await self.check_balance(session)
                await asyncio.sleep(uniform(1.0, 1.5))
                return True
            


    async def start(self):
        logger.info(f"Account {self.name} | started")
        connector = self.proxy.get_connector() if isinstance(self.proxy, Proxy) else None
        client = CloudflareScraper(headers=self.headers, connector=connector)
        async with client as session:
            while True:
                try:
                    if not self.tg_session.is_connected:
                        await self.tg_app_start()
                    await self.refresh_jwt_token(session)
                    await self.refresh_access_token(session)
                    self.logged = True
                    # Check balance
                    await self.check_balance(session)
                    await asyncio.sleep(2)

                    # Check daily reward
                    await self.daily_reward(session)
                    
                    # Check 8-hour farming and claim and start new
                    if bool(self.settings.CLAIM_FARMING):
                        res = await self.claim_farming(session)
                        if res:
                            await asyncio.sleep(2)
                            await self.start_farming(session)

                    # Start games and finish them
                    games_count = randint(self.settings.MIN_USE_PASSES, self.settings.MAX_USE_PASSES)
                    if games_count > self.passes:
                        games_count = self.passes
                    logger.info(f"{self.name} | <light-green>Start {games_count} games</light-green>")
                    while True:
                        try:
                            if not self.tg_session.is_connected:
                                await self.tg_app_start()
                            await self.refresh_jwt_token(session)
                            await self.refresh_access_token(session)
                            self.logged = True

                            if self.passes <= 0:
                                await self.check_balance(session)
                                logger.info(f"{self.name} | <light-green>Passes not found</light-green>")
                                break
                            if games_count <= 0:
                                await self.check_balance(session)
                                logger.info(f"{self.name} | <light-green>Games count empty</light-green>")
                                break

                            self.passes -= 1
                            games_count -= 1
                            game_id = await self.start_game(session)
                            sleep = uniform(self.settings.GAME_TIME[0], self.settings.GAME_TIME[1])
                            logger.info(f"{self.name} | Wait <cyan>{sleep}s</cyan> to finish game...")
                            await asyncio.sleep(sleep)
                            points = randint(self.settings.GAME_POINTS[0], self.settings.GAME_POINTS[1])
                            res = await self.claim_reward(session, game_id, points)
                            if not res:
                                await asyncio.sleep(2)
                                await self.check_balance(session)
                                raise Exception("Claim reward error")
                            await asyncio.sleep(randint(2, 10))

                        except Exception as e:
                            logger.error(f"{self.name} | Error: {e} account: {self.name} stopping...")
                            return

                    sleep = randint(3600*8 , 3600 * 9)
                    logger.info(f"Account {self.name} | Antifrost period | Sleep {sleep}s...")
                    await asyncio.sleep(sleep)

                    # Sleep until next night
                    await self.night_sleep_check()  
                except ClaimRewardError as e:
                    await self.check_balance(session)
                    logger.warning(f"{self.name} | <yellow>Claim reward failed: {e})</yellow>")
                    asyncio.sleep(uniform(1.0, 1.5*3600))

                except Exception as e:
                    logger.error(f"{self.name} | Error: {e}")
                    return

        logger.info(f"Account {self.name} | finished")


async def run_gamer(tg_session: tuple[Client, Proxy, str], settings) -> None:
    """
    Starts a Gamer instance and waits for a random time between 1-5 seconds before doing so.
    
    Args:
        tg_session (tuple[Client, Proxy, str]): A tuple containing a Client instance, a Proxy instance and a User-Agent string.
        settings (Settings): The settings to use for this Gamer instance.
    """
    tg_session, proxy, user_agent = tg_session
    gamer = Blum(tg_session=tg_session, settings=settings, proxy=proxy, user_agent=user_agent)
    try:
        sleep = randint(1, 5)
        logger.info(f"Account {gamer.name} | ready in {sleep}s")
        await asyncio.sleep(sleep)
        await gamer.start()
    except Exception as e:
        logger.error(f"Account {gamer.name} | Error: {e}")