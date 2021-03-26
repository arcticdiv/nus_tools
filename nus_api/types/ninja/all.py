from typing import Optional

from .._base import BaseType
from ... import reqdata, sources, utils


#####
# /<region>/title/<id>ec_info
#####

class NinjaEcInfo(BaseType['sources.Ninja']):
    title_id: str
    content_size: int
    version: int
    download_disabled: bool

    def __init__(self, source: 'sources.Ninja', content_id: str):
        super().__init__(
            source,
            reqdata.ReqData(path=f'{source.region}/title/{content_id}/ec_info')
        )

    def _read(self, iterator):
        ec_info = utils.xml.read_iterator_object(iterator, 'title_ec_info')
        utils.xml.validate_schema(ec_info, {'title_id': None, 'content_size': None, 'title_version': None, 'disable_download': None}, False)

        self.title_id = ec_info.title_id.text
        self.content_size = int(ec_info.content_size.text)
        self.version = int(ec_info.title_version.text)
        self.download_disabled = utils.misc.get_bool(ec_info.disable_download.text)


#####
# /titles/id_pair
#####

class NinjaIDPair(BaseType['sources.Ninja']):
    content_id: str
    title_id: str

    def __init__(self, source: 'sources.Ninja', content_id: Optional[str] = None, title_id: Optional[str] = None):
        if bool(content_id) == bool(title_id):
            raise ValueError('Exactly one of `content_id`/`title_id` must be set')
        # this endpoint probably supports multiple IDs at once, maybe consider implementing that as well
        super().__init__(
            source,
            reqdata.ReqData(
                path=f'titles/id_pair',
                params={'title_id[]': title_id} if title_id else {'ns_uid[]': content_id}
            )
        )

    def _read(self, iterator):
        pairs = utils.xml.read_iterator_object(iterator, 'title_id_pairs')
        assert len(pairs.getchildren()) == 1
        utils.xml.validate_schema(pairs, {'title_id_pair': {'ns_uid': None, 'title_id': None, 'type': None}}, False)
        pair = pairs.title_id_pair

        assert pair.type.text == 'T'  # not sure if there are any other types
        self.content_id = pair.ns_uid.text
        self.title_id = pair.title_id.text
