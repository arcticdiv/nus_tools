import reqcli.utils.xml as xmlutils
from typing import List, Optional, Tuple
from reqcli.type import BaseTypeLoadable

from ... import ids


class UpdateListVersion(BaseTypeLoadable):
    latest: int
    fqdn: str

    def _read(self, reader, config):
        info = xmlutils.read_object(reader)
        assert info.tag == 'version_list_info'
        xmlutils.validate_schema(info, {'version': None, 'fqdn': None}, False)

        self.latest = int(info.version.text)
        self.fqdn = info.fqdn.text


class UpdateList(BaseTypeLoadable):
    updates: List[Tuple[ids.TitleID, int]]

    def __init__(self, version: Optional[int] = None):
        self.__version = version
        super().__init__()

    def _read(self, reader, config):
        versionlist = xmlutils.read_object(reader)
        assert versionlist.tag == 'version_list'
        xmlutils.validate_schema(versionlist, {'version': None, 'titles': {'title': {'id': None, 'version': None}}}, True)

        # sanity check
        if self.__version is not None:
            assert int(versionlist.version.text) == self.__version

        if hasattr(versionlist.titles, 'title'):
            self.updates = [(ids.TitleID(title.id.text), int(title.version.text)) for title in versionlist.titles.title]
        else:
            self.updates = []
