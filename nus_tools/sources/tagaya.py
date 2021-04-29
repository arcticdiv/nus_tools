from typing import Any, Optional
from reqcli.source import BaseSource, SourceConfig, ReqData

from ..types.tagaya import UpdateListVersion, UpdateList


class _TagayaBase(BaseSource):
    # /latest_version
    def get_latest_updatelist_version(self, *, skip_cache: bool = True, **kwargs: Any) -> UpdateListVersion:
        return self._create_type(
            ReqData(path='latest_version'),
            UpdateListVersion(),
            skip_cache=skip_cache,
            **kwargs
        )

    # /list/<version>.versionlist
    def get_updatelist(self, version: int, **kwargs: Any) -> UpdateList:
        return self._create_type(
            ReqData(path=f'list/{version}.versionlist'),
            UpdateList(),
            **kwargs
        )


# region does not matter, lists are identical

class TagayaCDN(_TagayaBase):
    def __init__(self, config: Optional[SourceConfig] = None):
        super().__init__(
            ReqData(
                path='https://tagaya-wup.cdn.nintendo.net/tagaya/versionlist/EUR/EU/'
            ),
            config,
            verify_tls=False,
            require_fingerprint='43:8D:A9:4A:60:CB:00:DF:F2:B3:EB:17:A7:A2:1C:98:BD:11:FC:4A:A6:49:62:C1:2C:EF:41:BB:1F:28:88:95'
        )


class TagayaNoCDN(_TagayaBase):
    def __init__(self, config: Optional[SourceConfig] = None):
        super().__init__(
            ReqData(
                path='https://tagaya.wup.shop.nintendo.net/tagaya/versionlist/EUR/EU/'
            ),
            config,
            verify_tls=False,
            require_fingerprint='C6:6E:7D:66:D0:73:62:2F:A3:28:7F:A6:2F:F5:73:5C:71:EE:EB:3D:93:AC:B3:14:7A:8F:85:B4:07:D4:CE:ED'
        )
