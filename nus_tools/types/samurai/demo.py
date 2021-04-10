from typing import Optional

from . import common
from .._base import BaseTypeLoadable
from ... import utils


class SamuraiDemo(BaseTypeLoadable):
    name: str
    rating_info: common.SamuraiRatingDetailed
    icon_url: Optional[str] = None

    def _read(self, reader, config):
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
