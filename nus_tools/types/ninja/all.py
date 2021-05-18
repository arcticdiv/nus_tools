from typing import Optional
import reqcli.utils.xml as xmlutils
from reqcli.type import BaseTypeLoadable

from ... import utils, ids


class NinjaEcInfo(BaseTypeLoadable):
    title_id: ids.TitleID
    content_size: int
    version: int
    download_disabled: bool

    # 3DS only
    seed_published: Optional[bool]
    external_seed: Optional[str]
    playable_date: Optional[str]

    def _read(self, reader, config):
        ec_info = xmlutils.load_root(reader, 'title_ec_info')
        xmlutils.validate_schema(ec_info, {'title_id': None, 'content_size': None, 'title_version': None, 'disable_download': None, 'content_lock': {'seed_published': None, 'external_seed': None, 'playable_date': None}}, True)

        self.title_id = ids.TitleID(ec_info.title_id.text)
        self.content_size = int(ec_info.content_size.text)
        self.version = int(ec_info.title_version.text)
        self.download_disabled = utils.misc.get_bool(ec_info.disable_download.text)

        if hasattr(ec_info, 'content_lock'):
            self.seed_published = utils.misc.get_bool(ec_info.content_lock.seed_published.text)
            self.external_seed = xmlutils.get_text(ec_info.content_lock, 'external_seed')
            self.playable_date = xmlutils.get_text(ec_info.content_lock, 'playable_date')


class NinjaIDPair(BaseTypeLoadable):
    content_id: ids.ContentID
    title_id: ids.TitleID

    def _read(self, reader, config):
        pairs = xmlutils.load_root(reader, 'title_id_pairs')
        xmlutils.validate_schema(pairs, {'title_id_pair': {'ns_uid': None, 'title_id': None, 'type': None}}, False)
        assert len(pairs.getchildren()) == 1
        pair = pairs.title_id_pair

        assert pair.type.text in ('T', 'D')  # 'Title'/'Demo'?  # not sure if there are any other types
        self.content_id = ids.ContentID(pair.ns_uid.text)
        self.title_id = ids.TitleID(pair.title_id.text)
