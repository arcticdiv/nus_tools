from typing import Optional

from . import common
from .._base import BaseType
from ... import reqdata, sources, utils


#####
# /demo/<id>
#####

class SamuraiDemo(BaseType['sources.Samurai']):
    name: str
    rating_info: common.SamuraiRatingDetailed
    icon_url: Optional[str] = None

    def __init__(self, source: 'sources.Samurai', content_id: str):
        super().__init__(
            source,
            reqdata.ReqData(path=f'demo/{content_id}')
        )

    def _read(self, iterator):
        content = utils.xml.read_iterator_object(iterator, 'content')
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