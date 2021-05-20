from typing import Optional

import reqcli.utils.xml as xmlutils
from reqcli.type import BaseTypeLoadable

from . import common


class SamuraiDemo(BaseTypeLoadable):
    name: str
    rating_info: Optional[common.SamuraiRatingDetailed] = None
    icon_url: Optional[str] = None

    def _read(self, reader, config):
        content = xmlutils.load_root(reader, 'content')
        assert len(content.getchildren()) == 1
        demo = content.demo

        xmlutils.validate_schema(demo, {'name': None, 'icon_url': None, 'rating_info': common.SamuraiRatingDetailed._get_schema()[0]}, True)
        for child, tag, text in xmlutils.iter_children(demo):
            if tag == 'name':
                self.name = text
            elif tag == 'icon_url':
                self.icon_url = text
            elif tag == 'rating_info':
                self.rating_info = common.SamuraiRatingDetailed._parse(child)
            else:
                raise ValueError(f'unknown tag: {tag}')
