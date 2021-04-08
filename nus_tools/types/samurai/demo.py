from typing import Optional

from . import common
from .._base import BaseTypeLoadable
from ... import reqdata, sources, utils, ids


#####
# /demo/<id>
#####

class SamuraiDemo(BaseTypeLoadable['sources.Samurai']):
    name: str
    rating_info: common.SamuraiRatingDetailed
    icon_url: Optional[str] = None

    def __init__(self, source: 'sources.Samurai', content_id: ids.TContentIDInput):
        super().__init__(
            source,
            reqdata.ReqData(path=f'demo/{ids.ContentID.get_str(content_id)}')
        )

    def _read(self, reader):
        content = utils.xml.load_from_reader(reader, 'content')
        assert len(content.getchildren()) == 1
        demo = content.demo

        utils.xml.validate_schema(demo, {'name': None, 'icon_url': None, 'rating_info': common.SamuraiRatingDetailed._get_schema()[0]}, True)
        for child, tag, text in utils.xml.iter_children(demo):
            if tag == 'name':
                self.name = text
            elif tag == 'icon_url':
                self.icon_url = text
            elif tag == 'rating_info':
                self.rating_info = common.SamuraiRatingDetailed._parse(child)
            else:
                raise ValueError(f'unknown tag: {tag}')