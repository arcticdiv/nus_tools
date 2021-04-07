from typing import Optional, cast

from .._base import BaseTypeLoadable
from ... import reqdata, sources, utils, ids


#####
# /<region>/title/<id>/ec_info
#####

class NinjaEcInfo(BaseTypeLoadable['sources.Ninja']):
    title_id: ids.TitleID
    content_size: int
    version: int
    download_disabled: bool

    def __init__(self, source: 'sources.Ninja', content_id: ids.TContentIDInput):
        super().__init__(
            source,
            reqdata.ReqData(path=f'{source.region}/title/{ids.ContentID.get_str(content_id)}/ec_info')
        )

    def _read(self, reader):
        ec_info = utils.xml.load_from_reader(reader, 'title_ec_info')
        utils.xml.validate_schema(ec_info, {'title_id': None, 'content_size': None, 'title_version': None, 'disable_download': None}, False)

        self.title_id = ids.TitleID(ec_info.title_id.text)
        self.content_size = int(ec_info.content_size.text)
        self.version = int(ec_info.title_version.text)
        self.download_disabled = utils.misc.get_bool(ec_info.disable_download.text)


#####
# /titles/id_pair
#####

class NinjaIDPair(BaseTypeLoadable['sources.Ninja']):
    content_id: ids.ContentID
    title_id: ids.TitleID

    def __init__(self, source: 'sources.Ninja', *, content_id: Optional[ids.TContentIDInput] = None, title_id: Optional[ids.TTitleIDInput] = None):
        if (content_id is None) == (title_id is None):
            raise ValueError('Exactly one of `content_id`/`title_id` must be set')
        # this endpoint probably supports multiple IDs at once, maybe consider implementing that as well
        super().__init__(
            source,
            reqdata.ReqData(
                path='titles/id_pair',
                params={'title_id[]': ids.TitleID.get_str(title_id)} if title_id else {'ns_uid[]': ids.ContentID.get_str(cast(ids.TContentIDInput, content_id))}
            )
        )

    def _read(self, reader):
        pairs = utils.xml.load_from_reader(reader, 'title_id_pairs')
        assert len(pairs.getchildren()) == 1
        utils.xml.validate_schema(pairs, {'title_id_pair': {'ns_uid': None, 'title_id': None, 'type': None}}, False)
        pair = pairs.title_id_pair

        assert pair.type.text == 'T'  # not sure if there are any other types
        self.content_id = ids.ContentID(pair.ns_uid.text)
        self.title_id = ids.TitleID(pair.title_id.text)
