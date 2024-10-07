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


    CHANCE_TO_WIN: int = 80
    NIGHT_SLEEP: int = 1

    ROUND_COUNT_EACH_GAME: list[int] = [2, 5]        # in rounds for each game
    TIME_TO_PLAY_EACH_GAME: list[int] = [30, 90]     # in seconds for each game


    DELAY_EACH_ACCOUNT: list[int] = [20, 30]


settings = Settings()

async def main():
    try:
        await main_process(settings)
    except Exception as e:
        print(f"Error process: {e}")

if __name__ == '__main__':
    with suppress(KeyboardInterrupt):
        asyncio.run(main())

