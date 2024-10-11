import os
import shutil
from pydantic_settings import BaseSettings
from pyrogram import Client
from bot.utils.logger import logger
from bot.utils.proxy import Proxy
from bot.utils.headers import BrowserType, DeviceType, UserAgent, headers_example

class SessionExistsError(BaseException):
    pass

class SessionCreator:
    def __init__(self, settings: BaseSettings):
        self.__API_ID: int = settings.API_ID
        self.__API_HASH: str = settings.API_HASH
        if not self.__API_ID or not self.__API_HASH:
            raise ValueError("API_ID and API_HASH must be set in .env file")
        self.name: str = ""
        if not self.check_path():
            raise SessionExistsError("Session already exists, please try again")
        self.headers, self.user_agent = self.geterate_user_agent()
        self.proxy: None | Proxy = None

    def input_name(self) -> str:
        self.name = input('➤ ')
        if not self.name:
            raise ValueError("Name is required")
        return self.name
    
    def check_path(self) -> bool:
        print("Enter session name (or press Enter to exit): ")
        self.name = input('➤ ')
        if not self.name:
            return False
        if not os.path.exists('sessions'):
            os.mkdir('sessions')
        if os.path.exists(f'sessions/{self.name}'):
            return False
        return True
    
    def geterate_user_agent(self) -> tuple:
        headers = headers_example.copy()
        user_agent = UserAgent(device=DeviceType.ANDROID,
                                browser=BrowserType.CHROME).generate()
        headers['User-Agent'] = user_agent
        return headers, user_agent
    
    async def add_proxy(self):
        while True:
            print("┌──────────────────────────────────────────────┐")
            print("│   Enter proxy (or press Enter to use your    │")
            print("│        default IP without a proxy)           │")
            print("├──────────────────────────────────────────────┤")
            print("│ Example:                                     │")
            print("│   socks5://login:password@ip:port            │")
            print("│   http://login:password@ip:port              │")
            print("└──────────────────────────────────────────────┘")
            self.proxy = input('➤ ').replace(' ', '')
            if not self.proxy:
                logger.info('Use default IP\n')
                self.proxy = None
                break
            self.proxy = Proxy().parse_proxy(self.proxy)
            if not self.proxy:
                logger.warning('Invalid proxy format, please try again\n')
                continue
            if isinstance(self.proxy, Proxy):
                res = await self.proxy.check_proxy(self.headers)
                if not res:
                    logger.error('Proxy check failed, please try again\n')
                    continue
                if res:
                    logger.success('Proxy added successfully\n')
                    break
            break
        
    def save_user_agent(self):
        with open(f'sessions/{self.name}/user-agent.txt', 'w') as f:
            f.write(self.user_agent)

    def save_proxy(self):
        print(self.proxy)
        if self.proxy is None:
            return
        with open(f'sessions/{self.name}/proxy.txt', 'w') as f:
            f.write(str(self.proxy))

    async def create_session(self) -> bool:  
        try:
            await self.add_proxy()
            proxy_pyrogram = self.proxy.get_proxy_for_pyrogram() if isinstance(self.proxy, Proxy) else None
            os.mkdir(f'sessions/{self.name}')
            session = Client(
                name='session',
                api_id=self.__API_ID,
                api_hash=self.__API_HASH,
                workdir=f"sessions/{self.name}",
                proxy=proxy_pyrogram)
            print(proxy_pyrogram)
            print(self.proxy)
            async with session:
                user_data = await session.get_me()
                logger.success(f'Session added successfully @{user_data.username} | id:{user_data.id}')
        except Exception as error:
            shutil.rmtree(f"sessions/{self.name}")
            logger.error(f"Session creation failed | Error: {error}")
            return False
        self.save_proxy()
        self.save_user_agent()
        return True
