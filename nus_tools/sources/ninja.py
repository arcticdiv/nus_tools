from typing import Optional, cast

from ._base import BaseSource, SourceConfig
from .. import reqdata, ids
from ..types.ninja import NinjaEcInfo, NinjaIDPair


class Ninja(BaseSource):
    def __init__(self, region: str, cert: reqdata.CertType, config: Optional[SourceConfig] = None):
        super().__init__(
            reqdata.ReqData(
                path='https://ninja.wup.shop.nintendo.net/ninja/ws/',
                cert=cert
            ),
            config,
            verify_tls=False
        )
        self.region = region

    # /<region>/title/<id>/ec_info
    def get_ec_info(self, content_id: ids.TContentIDInput) -> NinjaEcInfo:
        return self._create_type(
            reqdata.ReqData(path=f'{self.region}/title/{ids.ContentID.get_str(content_id)}/ec_info'),
            NinjaEcInfo()
        )

    # /titles/id_pair
    def get_id_pair(self, *, content_id: Optional[ids.TContentIDInput] = None, title_id: Optional[ids.TTitleIDInput] = None) -> NinjaIDPair:
        if (content_id is None) == (title_id is None):
            raise ValueError('Exactly one of `content_id`/`title_id` must be set')

        return self._create_type(
            reqdata.ReqData(
                path='titles/id_pair',
                params={'title_id[]': ids.TitleID.get_str(title_id)} if title_id else {'ns_uid[]': ids.ContentID.get_str(cast(ids.TContentIDInput, content_id))}
            ),
            NinjaIDPair()
        )

    def get_content_id(self, title_id: ids.TTitleIDInput) -> ids.ContentID:
        return self.get_id_pair(title_id=title_id).content_id

    def get_title_id(self, content_id: ids.TContentIDInput) -> ids.TitleID:
        return self.get_id_pair(content_id=content_id).title_id
