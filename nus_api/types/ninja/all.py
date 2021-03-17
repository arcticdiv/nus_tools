from .._base import BaseType
from ... import reqdata, sources, utils


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
        self.download_disabled = utils.get_bool(ec_info.disable_download.text)
