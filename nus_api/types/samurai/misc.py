from dataclasses import dataclass
from typing import List

from .._base import BaseType
from ... import reqdata, sources, utils


@dataclass
class SamuraiNewsImage:
    url: str
    type: str
    index: int
    width: int
    height: int


@dataclass
class SamuraiNewsEntry:
    headline: str
    description: str
    date: str
    images: List[SamuraiNewsImage]


class SamuraiNews(BaseType['sources.Samurai']):
    entries: List[SamuraiNewsEntry]

    def __init__(self, source: 'sources.Samurai'):
        super().__init__(
            source,
            reqdata.ReqData(path=f'news')
        )

    def _read(self, iterator):
        news_xml = utils.xml.read_iterator_object(iterator, 'news')
        utils.xml.validate_schema(news_xml, {'news_entry': {'headline': None, 'description': None, 'date': None, 'images': {'image': None}}}, True)
        self.entries = []
        for entry in news_xml.news_entry:
            if hasattr(entry, 'images'):
                images = [
                    SamuraiNewsImage(
                        image.get('url'),
                        image.get('type'),
                        int(image.get('index')),
                        int(image.get('width')),
                        int(image.get('height'))
                    )
                    for image in entry.images.image
                ]
            else:
                images = []
            self.entries.append(SamuraiNewsEntry(
                entry.headline.text,
                entry.description.text,
                entry.date.text,
                images
            ))
