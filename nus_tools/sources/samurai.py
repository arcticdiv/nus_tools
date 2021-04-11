from typing import Callable, Iterator, Optional, Type, TypeVar, Union, List, Tuple

from ..utils.typing import RequestDict

from ._base import BaseSource, SourceConfig
from .. import ids
from ..reqdata import ReqData
from ..types.samurai import \
    SamuraiContentsList, \
    SamuraiMovie, SamuraiMoviesList, \
    SamuraiTitle, SamuraiTitlesList, \
    SamuraiDlcWiiU, SamuraiDlcsWiiU, SamuraiTitleDlcsWiiU, SamuraiTitleDlcs3DS, SamuraiDlcSizes, SamuraiDlcPrices, \
    SamuraiDemo, \
    SamuraiNews, SamuraiTelops
from ..types.samurai._base import SamuraiListBaseType
from ..types.samurai.title_list import SamuraiListTitle
from ..types.samurai.title import SamuraiTitleElement


_TList = TypeVar('_TList', bound=SamuraiListBaseType)


class Samurai(BaseSource):
    def __init__(self, region: str, shop_id: int, lang: str, config: Optional[SourceConfig] = None):
        super().__init__(
            ReqData(
                path=f'https://samurai.wup.shop.nintendo.net/samurai/ws/{region}/',
                params={'shop_id': shop_id, 'lang': lang}
            ),
            config,
            verify_tls=False,
            require_fingerprint='C6:6E:7D:66:D0:73:62:2F:A3:28:7F:A6:2F:F5:73:5C:71:EE:EB:3D:93:AC:B3:14:7A:8F:85:B4:07:D4:CE:ED'
        )
        self.region = region
        self.shop_id = shop_id
        self.lang = lang

    # could use functools.partial for most of these, but type information would be lost

    # /contents
    def get_content_count(self, other_params: RequestDict = {}) -> int:
        return self._get_list_total(self.get_content_list, other_params)

    def get_content_list(self, offset: int, limit: int = 200, other_params: RequestDict = {}) -> SamuraiContentsList:
        return self._get_list(SamuraiContentsList, 'contents', offset, limit, other_params)

    def get_all_content_lists(self, max_page_size: int = 200, other_params: RequestDict = {}) -> Iterator[SamuraiContentsList]:
        return self._get_all_lists(self.get_content_list, max_page_size, other_params)

    # /title/<id>
    def get_title(self, content_id: ids.TContentIDInput) -> SamuraiTitle:
        return self._create_type(
            ReqData(path=f'title/{ids.ContentID.get_str(content_id)}'),
            SamuraiTitle()
        )

    # /titles
    def get_title_count(self, other_params: RequestDict = {}) -> int:
        return self._get_list_total(self.get_title_list, other_params)

    def get_title_list(self, offset: int, limit: int = 200, other_params: RequestDict = {}) -> SamuraiTitlesList:
        return self._get_list(SamuraiTitlesList, 'titles', offset, limit, other_params)

    def get_all_title_lists(self, max_page_size: int = 200, other_params: RequestDict = {}) -> Iterator[SamuraiTitlesList]:
        return self._get_all_lists(self.get_title_list, max_page_size, other_params)

    # movies
    def get_movie(self, content_id: ids.TContentIDInput) -> SamuraiMovie:
        return self._create_type(
            ReqData(path=f'movie/{ids.ContentID.get_str(content_id)}'),
            SamuraiMovie()
        )

    def get_movie_count(self, other_params: RequestDict = {}) -> int:
        return self._get_list_total(self.get_movie_list, other_params)

    def get_movie_list(self, offset: int, limit: int = 200, other_params: RequestDict = {}) -> SamuraiMoviesList:
        return self._get_list(SamuraiMoviesList, 'movies', offset, limit, other_params)

    def get_all_movie_lists(self, max_page_size: int = 200, other_params: RequestDict = {}) -> Iterator[SamuraiMoviesList]:
        return self._get_all_lists(self.get_movie_list, max_page_size, other_params)

    # /aocs
    # WiiU only since 3DS DLCs don't have their own content IDs
    def get_dlcs_wiiu(self, *dlc_ids: ids.TContentIDInput) -> SamuraiDlcsWiiU:
        for dlc_id in dlc_ids:
            dlc_id = ids.ContentID.get_inst(dlc_id)
            if dlc_id.type.platform != ids.ContentPlatform.WIIU:
                raise ValueError(f'content ID {dlc_id} is not a WiiU title')

        return self._create_type(
            ReqData(
                path='aocs',
                params={'aoc[]': ','.join(ids.ContentID.get_str(i) for i in dlc_ids)}
            ),
            SamuraiDlcsWiiU()
        )

    def get_dlcs_for_title(self, title: Union[ids.TContentIDInput, SamuraiListTitle, SamuraiTitleElement]) -> Union[SamuraiTitleDlcsWiiU, SamuraiTitleDlcs3DS]:
        if isinstance(title, (SamuraiListTitle, SamuraiTitleElement)):
            content_id = title.content_id
        else:
            content_id = ids.ContentID.get_inst(title)

        dlcs_type: Union[SamuraiTitleDlcs3DS, SamuraiTitleDlcsWiiU]
        if content_id.type.platform == ids.ContentPlatform._3DS:
            dlcs_type = SamuraiTitleDlcs3DS()
            params = {}  # 3DS DLC results aren't paginated
        elif content_id.type.platform == ids.ContentPlatform.WIIU:
            dlcs_type = SamuraiTitleDlcsWiiU()
            params = {'limit': 200}  # assuming a maximum of 200 DLCs per title, seems reasonable
        else:
            assert False  # unhandled, should never happen

        return self._create_type(
            ReqData(path=f'title/{ids.ContentID.get_str(content_id)}/aocs', params=params),
            dlcs_type
        )

    def get_dlc_sizes(self, *dlcs: Union[ids.TContentIDInput, SamuraiDlcWiiU]) -> SamuraiDlcSizes:
        return self._create_type(
            ReqData(
                path='aocs/size',
                params={'aoc[]': ','.join(ids.ContentID.get_str(i) for i in self.__get_dlc_ids(dlcs))}
            ),
            SamuraiDlcSizes()
        )

    def get_dlc_prices(self, *dlcs: Union[ids.TContentIDInput, SamuraiDlcWiiU]) -> SamuraiDlcPrices:
        return self._create_type(
            ReqData(
                path='aocs/prices',
                params={'aoc[]': ','.join(ids.ContentID.get_str(i) for i in self.__get_dlc_ids(dlcs))}
            ),
            SamuraiDlcPrices()
        )

    def __get_dlc_ids(self, dlcs: Tuple[Union[ids.TContentIDInput, SamuraiDlcWiiU], ...]) -> List[ids.TContentIDInput]:
        if len(dlcs) == 0:
            raise RuntimeError('no DLC content ID provided')
        return [d.content_id if isinstance(d, SamuraiDlcWiiU) else d for d in dlcs]

    # /demo/<id>
    def get_demo(self, content_id: ids.TContentIDInput) -> SamuraiDemo:
        return self._create_type(
            ReqData(path=f'demo/{ids.ContentID.get_str(content_id)}'),
            SamuraiDemo()
        )

    def get_demos(self, title: SamuraiTitleElement) -> List[SamuraiDemo]:
        if not title.demos:
            return []
        return [self.get_demo(demo.content_id) for demo in title.demos]

    # misc
    # /news
    def get_news(self) -> SamuraiNews:
        return self._create_type(
            ReqData(path='news'),
            SamuraiNews()
        )

    # /telops
    def get_telops(self) -> SamuraiTelops:
        return self._create_type(
            ReqData(path='telops'),
            SamuraiTelops()
        )

    # generic list funcs
    def _get_list(self, list_type: Type[_TList], path: str, offset: int, limit: int, other_params: RequestDict) -> _TList:
        return self._create_type(
            ReqData(path=path, params={'offset': offset, 'limit': limit, **other_params}),
            list_type()
        )

    def _get_list_total(self, get_list_func: Callable[[int, int, RequestDict], _TList], other_params: RequestDict) -> int:
        return get_list_func(0, 1, other_params).total

    def _get_all_lists(self, get_list_func: Callable[[int, int, RequestDict], _TList], max_page_size: int, other_params: RequestDict) -> Iterator[_TList]:
        first_page = get_list_func(0, max_page_size, other_params)
        yield first_page
        for offset in range(max_page_size, first_page.total, max_page_size):
            yield get_list_func(offset, max_page_size, other_params)
