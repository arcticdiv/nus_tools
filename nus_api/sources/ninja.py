from ._base import BaseSource, SourceConfig
from .. import reqdata
from ..types.ninja import NinjaEcInfo, NinjaIDPair


class Ninja(BaseSource):
    def __init__(self, region: str, cert: reqdata.CertType, config: SourceConfig = None):
        super().__init__(
            reqdata.ReqData(
                path=f'https://ninja.wup.shop.nintendo.net/ninja/ws/',
                cert=cert
            ),
            config,
            verify_tls=False
        )
        self.region = region

    def get_ec_info(self, content_id: str) -> NinjaEcInfo:
        return NinjaEcInfo(self, content_id).load()

    def get_content_id(self, title_id: str) -> str:
        return NinjaIDPair(self, title_id=title_id).load().content_id

    def get_title_id(self, content_id: str) -> str:
        return NinjaIDPair(self, content_id=content_id).load().title_id
