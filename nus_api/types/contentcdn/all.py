from typing import Optional

from .._base import BaseType
from ... import reqdata, structs
from ...sources import contentcdn as source_contentcdn


#####
# /<title id>/cetk
#####

class CETK(BaseType['source_contentcdn._BaseContentSource']):
    def __init__(self, source: 'source_contentcdn._BaseContentSource', title_id: str):
        super().__init__(
            source,
            reqdata.ReqData(path=f'{title_id}/cetk')
        )

    def _read(self, iterator):
        raw_data = iterator.read_all()
        self.struct = structs.cetk.parse(raw_data)


#####
# /<title id>/tmd[.<version>]
#####

class TMD(BaseType['source_contentcdn._BaseContentSource']):
    def __init__(self, source: 'source_contentcdn._BaseContentSource', title_id: str, version: Optional[int]):
        super().__init__(
            source,
            reqdata.ReqData(path=f'{title_id}/tmd' + (f'.{version}' if version is not None else ''))
        )

    def _read(self, iterator):
        raw_data = iterator.read_all()
        self.struct = structs.tmd.parse(raw_data)
