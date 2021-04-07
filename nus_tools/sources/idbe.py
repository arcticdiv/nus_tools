from typing import Optional

from ._base import BaseSource, SourceConfig
from .. import reqdata, ids
from ..types.idbe import IDBE


class IDBEServer(BaseSource):
    def __init__(self, platform: str, config: SourceConfig = None):
        if platform not in ('wup', 'ctr'):
            raise ValueError('`platform` must be either \'wup\' or \'ctr\'')
        super().__init__(
            reqdata.ReqData(
                path=f'https://idbe-{platform}.cdn.nintendo.net/icondata/'
            ),
            config,
            verify_tls=False
        )
        self.platform = platform

    def get_idbe(self, title_id: ids.TTitleIDInput, version: Optional[int] = None) -> IDBE:
        return IDBE(self, title_id, version).load()
