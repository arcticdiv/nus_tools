from ._base import BaseSource
from .. import reqdata
from ..types import NinjaEcInfo


class Ninja(BaseSource):
    def __init__(self, region: str, cert: reqdata.CertType):
        super().__init__(
            reqdata.ReqData(
                path=f'https://ninja.wup.shop.nintendo.net/ninja/ws/',
                cert=cert
            ),
            verify_tls=False
        )
        self.region = region

    def get_ec_info(self, content_id: str) -> NinjaEcInfo:
        return NinjaEcInfo(self, content_id).load()
