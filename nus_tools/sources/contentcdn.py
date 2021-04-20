from typing import Optional
from reqcli.source import UnloadableType, BaseSource, SourceConfig, ReqData

from .. import ids
from ..types.contentcdn import Ticket, TMD


class _BaseContentSource(BaseSource):
    # /<title id>/cetk
    def get_cetk(self, title_id: ids.TTitleIDInput) -> Ticket:
        return self._create_type(
            ReqData(path=f'{ids.TitleID.get_str(title_id)}/cetk'),
            Ticket(title_id)
        )

    # /<title id>/tmd[.<version>]
    def get_tmd(self, title_id: ids.TTitleIDInput, version: Optional[int] = None) -> TMD:
        return self._create_type(
            ReqData(path=f'{ids.TitleID.get_str(title_id)}/tmd' + (f'.{version}' if version is not None else '')),
            TMD(title_id)
        )

    # /<title id>/<content id>
    def get_app(self, title_id: ids.TTitleIDInput, content_id: int, *, skip_cache: bool = True) -> UnloadableType:
        return self._create_type(
            ReqData(path=f'{ids.TitleID.get_str(title_id)}/{content_id:08x}'),  # TODO: uppercase/lowercase?
            skip_cache=skip_cache
        )

    # /<title id>/<content id>.h3
    def get_h3(self, title_id: ids.TTitleIDInput, content_id: int) -> UnloadableType:
        return self._create_type(
            ReqData(path=f'{ids.TitleID.get_str(title_id)}/{content_id:08x}.h3')
        )


# there are multiple different servers, their purpose isn't entirely clear
# the domains resolve to different IPs, but the servers all seem to serve mostly the same contents (?)
# - cached/cdn:
#   - nus.cdn.c.shop.nintendowifi.net (unavailable)
#   - ccs.cdn.c.shop.nintendowifi.net
#   - nus.cdn.t.shop.nintendowifi.net
#   - ccs.cdn.t.shop.nintendowifi.net
#   - nus.cdn.wup.shop.nintendo.net
#   - ccs.cdn.wup.shop.nintendo.net
# - uncached:
#   - nus.c.shop.nintendowifi.net (unavailable)
#   - ccs.c.shop.nintendowifi.net (unavailable)
#   - nus.t.shop.nintendowifi.net (unavailable)
#   - ccs.t.shop.nintendowifi.net
#   - nus.wup.shop.nintendo.net (unavailable)
#   - ccs.wup.shop.nintendo.net

class CachedContentServer(_BaseContentSource):
    def __init__(self, config: Optional[SourceConfig] = None):
        super().__init__(
            ReqData(
                path='http://ccs.cdn.c.shop.nintendowifi.net/ccs/download/'
            ),
            config
        )


class UncachedContentServer(_BaseContentSource):
    def __init__(self, config: Optional[SourceConfig] = None):
        super().__init__(
            ReqData(
                path='http://ccs.wup.shop.nintendo.net/ccs/download/'
            ),
            config
        )
