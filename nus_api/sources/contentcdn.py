from typing import Optional

from ._base import BaseSource, SourceConfig
from .. import reqdata, ids
from ..types.contentcdn import CETK, TMD, APP, H3


class _BaseContentSource(BaseSource):
    def get_cetk(self, title_id: ids.TTitleIDInput) -> CETK:
        return CETK(self, title_id).load()

    def get_tmd(self, title_id: ids.TTitleIDInput, version: Optional[int] = None) -> TMD:
        return TMD(self, title_id, version).load()

    def get_app(self, title_id: ids.TTitleIDInput, content_id: int) -> APP:
        return APP(self, title_id, content_id)

    def get_h3(self, title_id: ids.TTitleIDInput, content_id: int) -> H3:
        return H3(self, title_id, content_id)


# there are multiple different servers, their purpose isn't entirely clear
# the domains resolve to different IPs, but the servers all seem to serve the same contents (?)
# - cached/cdn:
#   - nus.cdn.c.shop.nintendowifi.net (unavailable)
#   - ccs.cdn.c.shop.nintendowifi.net
#   - nus.cdn.wup.shop.nintendo.net
#   - ccs.cdn.wup.shop.nintendo.net
# - uncached:
#   - nus.c.shop.nintendowifi.net (unavailable)
#   - ccs.c.shop.nintendowifi.net (unavailable)
#   - nus.wup.shop.nintendo.net (unavailable)
#   - ccs.wup.shop.nintendo.net

class CachedContentServer(_BaseContentSource):
    def __init__(self, config: SourceConfig = None):
        super().__init__(
            reqdata.ReqData(
                path='http://ccs.cdn.wup.shop.nintendo.net/ccs/download/'
            ),
            config
        )


class UncachedContentServer(_BaseContentSource):
    def __init__(self, config: SourceConfig = None):
        super().__init__(
            reqdata.ReqData(
                path='http://ccs.wup.shop.nintendo.net/ccs/download/'
            ),
            config
        )
