from typing import Any, Optional, Union, cast
from reqcli.source import BaseSource, SourceConfig, CertType, ReqData

from .. import ids
from ..region import Region
from ..types.ninja import NinjaEcInfo, NinjaIDPair


class Ninja(BaseSource):
    def __init__(self, region: Union[str, Region], cert: CertType, config: Optional[SourceConfig] = None):
        super().__init__(
            ReqData(
                path='https://ninja.wup.shop.nintendo.net/ninja/ws/',
                cert=cert
            ),
            config,
            verify_tls=False,
            require_fingerprint='C6:6E:7D:66:D0:73:62:2F:A3:28:7F:A6:2F:F5:73:5C:71:EE:EB:3D:93:AC:B3:14:7A:8F:85:B4:07:D4:CE:ED'
        )

        self.region = region.country_code if isinstance(region, Region) else region

    # /<region>/title/<id>/ec_info
    def get_ec_info(self, content_id: ids.TContentIDInput, **kwargs: Any) -> NinjaEcInfo:
        return self._create_type(
            ReqData(path=f'{self.region}/title/{ids.ContentID.get_str(content_id)}/ec_info'),
            NinjaEcInfo(),
            **kwargs
        )

    # /titles/id_pair
    def get_id_pair(self, *, content_id: Optional[ids.TContentIDInput] = None, title_id: Optional[ids.TTitleIDInput] = None, **kwargs: Any) -> NinjaIDPair:
        if (content_id is None) == (title_id is None):
            raise ValueError('Exactly one of `content_id`/`title_id` must be set')

        return self._create_type(
            ReqData(
                path='titles/id_pair',
                params={'title_id[]': ids.TitleID.get_str(title_id)} if title_id else {'ns_uid[]': ids.ContentID.get_str(cast(ids.TContentIDInput, content_id))}
            ),
            NinjaIDPair(),
            **kwargs
        )

    def get_content_id(self, title_id: ids.TTitleIDInput, **kwargs: Any) -> ids.ContentID:
        return self.get_id_pair(title_id=title_id, **kwargs).content_id

    def get_title_id(self, content_id: ids.TContentIDInput, **kwargs: Any) -> ids.TitleID:
        return self.get_id_pair(content_id=content_id, **kwargs).title_id
