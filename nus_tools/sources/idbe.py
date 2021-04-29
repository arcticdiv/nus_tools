from typing import Any, Optional
from reqcli.source import BaseSource, SourceConfig, ReqData

from .. import ids
from ..types.idbe import IDBE


class IDBEServer(BaseSource):
    def __init__(self, platform: str, config: Optional[SourceConfig] = None):
        # platform does not matter, both servers seem to contain the same data
        if platform not in ('wup', 'ctr'):
            raise ValueError('`platform` must be either \'wup\' or \'ctr\'')
        super().__init__(
            ReqData(
                path=f'https://idbe-{platform}.cdn.nintendo.net/icondata/'
            ),
            config,
            verify_tls=False,
            # fingerprints for ctr/wup certs are the same
            require_fingerprint='43:8D:A9:4A:60:CB:00:DF:F2:B3:EB:17:A7:A2:1C:98:BD:11:FC:4A:A6:49:62:C1:2C:EF:41:BB:1F:28:88:95'
        )
        self.platform = platform

    # /<id>/<title id>.idbe
    def get_idbe(self, title_id: ids.TTitleIDInput, version: Optional[int] = None, **kwargs: Any) -> IDBE:
        tid_str = ids.TitleID.get_str(title_id)
        return self._create_type(
            # server seems to ignore first value, it probably doesn't matter what is supplied here
            # based on nn_idbe.rpl .text+0x1d0
            ReqData(path=f'{tid_str[12:14]}/{tid_str}' + (f'-{version}' if version is not None else '') + '.idbe'),
            IDBE(title_id),
            **kwargs
        )
