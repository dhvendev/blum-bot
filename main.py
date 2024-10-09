import asyncio
from contextlib import suppress
from bot.main import main_process
from bot.utils.proxy import Proxy
from pydantic_settings import BaseSettings, SettingsConfigDict



class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: int
    API_HASH: str
    REF: str
    CLAIM_FARMING: int = 1
    NIGHT_SLEEP: int = 1
    MIN_USE_PASSES: int = 5
    MAX_USE_PASSES: int = 9

    GAME_TIME: list = [35, 45]
    GAME_POINTS: list = [120, 190]

settings = Settings()

async def main():
    try:
        await main_process(settings)
    except Exception as e:
        print(f"Error process: {e}")

if __name__ == '__main__':
    with suppress(KeyboardInterrupt):
        asyncio.run(main())

