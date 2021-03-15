from dataclasses import dataclass


@dataclass
class __Configuration:
    cache_path: str = './cache/'
    default_user_agent: str = ''  # TODO


Configuration = __Configuration()
