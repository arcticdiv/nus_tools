from typing import Iterator, Type, TypeVar, Union, List

from ._base import BaseSource, SourceConfig
from ..reqdata import ReqData
from ..types.samurai import \
    SamuraiContentsList, \
    SamuraiMovie, SamuraiMoviesList, \
    SamuraiTitle, SamuraiTitlesList, \
    SamuraiDlcsWiiU, SamuraiDlcs3DS, \
    SamuraiDemo, \
    SamuraiNews, SamuraiTelops
from ..types.samurai._base import SamuraiListBaseType
from ..types.samurai.title_list import SamuraiListTitle
from ..types.samurai.title import SamuraiTitleElement


_TList = TypeVar('_TList', bound=SamuraiListBaseType)


class Samurai(BaseSource):
    def __init__(self, region: str, shop_id: int, lang: str, config: SourceConfig = None):
        super().__init__(
            ReqData(
                path=f'https://samurai.wup.shop.nintendo.net/samurai/ws/{region}/',
                params={'shop_id': shop_id, 'lang': lang}
            ),
            config,
            verify_tls=False
        )
        self.region = region
        self.shop_id = shop_id
        self.lang = lang

    # could use functools.partial for most of these, but type information would be lost

    # contents
    def get_content_count(self, other_params: dict = {}) -> int:
        return self._get_list_total(SamuraiContentsList, other_params)

    def get_content_list(self, offset: int, limit: int = 200, other_params: dict = {}) -> SamuraiContentsList:
        return self._get_list(SamuraiContentsList, offset, limit, other_params)

    def get_all_content_lists(self, max_page_size: int = 200, other_params: dict = {}) -> Iterator[SamuraiContentsList]:
        return self._get_all_lists(SamuraiContentsList, max_page_size, other_params)

    # titles
    def get_title(self, eshop_id: str) -> SamuraiTitle:
        return SamuraiTitle(self, eshop_id).load()

    def get_title_count(self, other_params: dict = {}) -> int:
        return self._get_list_total(SamuraiTitlesList, other_params)

    def get_title_list(self, offset: int, limit: int = 200, other_params: dict = {}) -> SamuraiTitlesList:
        return self._get_list(SamuraiTitlesList, offset, limit, other_params)

    def get_all_title_lists(self, max_page_size: int = 200, other_params: dict = {}) -> Iterator[SamuraiTitlesList]:
        return self._get_all_lists(SamuraiTitlesList, max_page_size, other_params)

    # movies
    def get_movie(self, eshop_id: str) -> SamuraiMovie:
        return SamuraiMovie(self, eshop_id).load()

    def get_movie_count(self, other_params: dict = {}) -> int:
        return self._get_list_total(SamuraiMoviesList, other_params)

    def get_movie_list(self, offset: int, limit: int = 200, other_params: dict = {}) -> SamuraiMoviesList:
        return self._get_list(SamuraiMoviesList, offset, limit, other_params)

    def get_all_movie_lists(self, max_page_size: int = 200, other_params: dict = {}) -> Iterator[SamuraiMoviesList]:
        return self._get_all_lists(SamuraiMoviesList, max_page_size, other_params)

    # dlcs
    def get_dlcs(self, title: Union[str, SamuraiListTitle, SamuraiTitleElement]) -> Union[SamuraiDlcsWiiU, SamuraiDlcs3DS]:
        if isinstance(title, str):
            content_id = title
        else:
            content_id = title.content_id
        if content_id.startswith('5'):  # TODO: improve this
            return SamuraiDlcs3DS(self, content_id).load()
        else:
            return SamuraiDlcsWiiU(self, content_id).load()

    # demos
    def get_demo(self, content_id: str) -> SamuraiDemo:
        return SamuraiDemo(self, content_id).load()

    def get_demos(self, title: SamuraiTitleElement) -> List[SamuraiDemo]:
        if not title.demos:
            return []
        return [self.get_demo(demo.content_id) for demo in title.demos]

    # misc
    def get_news(self) -> SamuraiNews:
        return SamuraiNews(self).load()

    def get_telops(self) -> SamuraiTelops:
        return SamuraiTelops(self).load()

    # abstract list funcs
    def _get_list(self, list_type: Type[_TList], offset: int, limit: int, other_params: dict) -> _TList:
        return list_type(self, offset, limit, other_params).load()

    def _get_list_total(self, list_type: Type[_TList], other_params: dict) -> int:
        return self._get_list(list_type, 0, 1, other_params).total

    def _get_all_lists(self, list_type: Type[_TList], max_page_size: int, other_params: dict) -> Iterator[_TList]:
        first_page = self._get_list(list_type, 0, max_page_size, other_params)
        yield first_page
        for offset in range(max_page_size, first_page.total, max_page_size):
            yield self._get_list(list_type, offset, max_page_size, other_params)
