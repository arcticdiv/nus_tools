from typing import Any, Optional
from reqcli.source import UnloadableType, BaseSource, SourceConfig, ReqData, CertType

from .. import ids
from ..types.contentcdn import Ticket, TMD


class _ContentServerBase(BaseSource):
    # /<title id>/cetk
    def get_cetk(self, title_id: ids.TTitleIDInput, **kwargs: Any) -> Ticket:
        return self._create_type(
            ReqData(path=f'{ids.TitleID.get_str(title_id)}/cetk'),
            Ticket(title_id),
            **kwargs
        )

    # /<title id>/tmd[.<version>]
    def get_tmd(self, title_id: ids.TTitleIDInput, version: Optional[int] = None, **kwargs: Any) -> TMD:
        return self._create_type(
            ReqData(path=f'{ids.TitleID.get_str(title_id)}/tmd' + (f'.{version}' if version is not None else '')),
            TMD(title_id),
            **kwargs
        )

    # /<title id>/<content id>
    def get_app(self, title_id: ids.TTitleIDInput, content_id: int, *, skip_cache: bool = True, **kwargs: Any) -> UnloadableType:
        return self._create_type(
            ReqData(path=f'{ids.TitleID.get_str(title_id)}/{content_id:08X}'),
            skip_cache=skip_cache,
            **kwargs
        )

    # /<title id>/<content id>.h3
    def get_h3(self, title_id: ids.TTitleIDInput, content_id: int, **kwargs: Any) -> UnloadableType:
        return self._create_type(
            ReqData(path=f'{ids.TitleID.get_str(title_id)}/{content_id:08X}.h3'),
            **kwargs
        )


# there are multiple different servers, their purpose isn't entirely clear
# the domains resolve to different IPs, but the servers all seem to serve mostly the same contents (?)
# - cached/cdn:
#   - nus.cdn.c.shop.nintendowifi.net (unavailable)
#   - ccs.cdn.c.shop.nintendowifi.net
#   - nus.cdn.t.shop.nintendowifi.net
#   - ccs.cdn.t.shop.nintendowifi.net
#   - nus.cdn.wup.shop.nintendo.net (WiiU: 'SystemContentPrefixURL')
#   - ccs.cdn.wup.shop.nintendo.net (WiiU: 'ContentPrefixURL')
# - uncached:
#   - nus.c.shop.nintendowifi.net (unavailable)
#   - ccs.c.shop.nintendowifi.net (https only)
#   - nus.t.shop.nintendowifi.net (unavailable)
#   - ccs.t.shop.nintendowifi.net
#   - nus.wup.shop.nintendo.net (unavailable)
#   - ccs.wup.shop.nintendo.net (WiiU: 'UncachedContentPrefixURL'/'SystemUncachedContentPrefixURL')

class ContentServerWiiUCDN(_ContentServerBase):
    def __init__(self, config: Optional[SourceConfig] = None):
        super().__init__(
            ReqData(path='http://ccs.cdn.wup.shop.nintendo.net/ccs/download/'),
            config
        )


class ContentServerWiiUNoCDN(_ContentServerBase):
    def __init__(self, config: Optional[SourceConfig] = None):
        super().__init__(
            ReqData(path='http://ccs.wup.shop.nintendo.net/ccs/download/'),
            config
        )


class ContentServer3DSCDN(_ContentServerBase):
    def __init__(self, config: Optional[SourceConfig] = None):
        super().__init__(
            ReqData(path='http://ccs.cdn.c.shop.nintendowifi.net/ccs/download/'),
            config
        )


class ContentServer3DSNoCDN(_ContentServerBase):
    def __init__(self, cert: CertType, config: Optional[SourceConfig] = None):
        super().__init__(
            ReqData(path='https://ccs.c.shop.nintendowifi.net/ccs/download/', cert=cert),
            config,
            verify_tls=False,
            require_fingerprint='E9:74:4D:71:E3:06:6A:84:80:1D:0B:52:5E:26:8E:80:70:41:F4:20'
        )
