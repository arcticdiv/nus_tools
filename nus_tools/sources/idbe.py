from typing import Optional

from ._base import BaseSource, SourceConfig
from .. import reqdata, ids
from ..types.idbe import IDBE


class IDBEServer(BaseSource):
    def __init__(self, platform: str, config: Optional[SourceConfig] = None):
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

    # /<id>/<title id>.idbe
    def get_idbe(self, title_id: ids.TTitleIDInput, version: Optional[int] = None) -> IDBE:
        tid_str = ids.TitleID.get_str(title_id)
        return self._create_type(
            # server seems to ignore first value, it probably doesn't matter what is supplied here
            # based on nn_idbe.rpl .text+0x1d0
            reqdata.ReqData(path=f'{tid_str[12:14]}/{tid_str}' + (f'-{version}' if version is not None else '') + '.idbe'),
            IDBE(title_id)
        )
