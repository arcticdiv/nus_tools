from .._base import BaseTypeLoadable
from ... import utils, ids


class NinjaEcInfo(BaseTypeLoadable):
    title_id: ids.TitleID
    content_size: int
    version: int
    download_disabled: bool

    def _read(self, reader, config):
        ec_info = utils.xml.load_from_reader(reader, 'title_ec_info')
        utils.xml.validate_schema(ec_info, {'title_id': None, 'content_size': None, 'title_version': None, 'disable_download': None}, False)

        self.title_id = ids.TitleID(ec_info.title_id.text)
        self.content_size = int(ec_info.content_size.text)
        self.version = int(ec_info.title_version.text)
        self.download_disabled = utils.misc.get_bool(ec_info.disable_download.text)


class NinjaIDPair(BaseTypeLoadable):
    content_id: ids.ContentID
    title_id: ids.TitleID

    def _read(self, reader, config):
        pairs = utils.xml.load_from_reader(reader, 'title_id_pairs')
        assert len(pairs.getchildren()) == 1
        utils.xml.validate_schema(pairs, {'title_id_pair': {'ns_uid': None, 'title_id': None, 'type': None}}, False)
        pair = pairs.title_id_pair

        assert pair.type.text == 'T'  # not sure if there are any other types
        self.content_id = ids.ContentID(pair.ns_uid.text)
        self.title_id = ids.TitleID(pair.title_id.text)
