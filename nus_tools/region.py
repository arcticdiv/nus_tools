from enum import Enum


class Region(Enum):
    EUR, USA, JPN, KOR = range(4)
    ALL = 255

    @property
    def country_code(self) -> str:
        try:
            return {
                Region.EUR: 'GB',
                Region.USA: 'US',
                Region.JPN: 'JP',
                Region.KOR: 'KR'
            }[self]
        except KeyError:
            raise RuntimeError(f'{self} does not have a country code')
