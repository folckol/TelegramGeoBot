from environs import Env
from dataclasses import dataclass

@dataclass
class Bots:
    bot_token: str
    api_hash: str
    api_id: int

@dataclass
class Settings:
    bots: Bots

def get_settings(path: str):
    TOKEN = ''
    API_HASH = ''
    API_ID = ''

    with open(path, 'r') as file:
        for i in file:
            if 'TOKEN=' in i:
                TOKEN = i.rstrip().split('TOKEN=')[-1]
            elif 'API_HASH=' in i:
                API_HASH = i.rstrip().split('API_HASH=')[-1]
            elif 'API_ID=' in i:
                API_ID = i.rstrip().split('API_ID=')[-1]


    return Settings(
        bots=Bots(
            bot_token=TOKEN,
            api_hash=API_HASH,
            api_id=API_ID
        )
    )
settings = get_settings('env/config/input')
