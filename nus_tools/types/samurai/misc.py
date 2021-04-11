from dataclasses import dataclass
from typing import List

from .._base import BaseTypeLoadable
from ... import utils


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


class SamuraiNews(BaseTypeLoadable):
    entries: List[SamuraiNewsEntry]

    def _read(self, reader, config):
        news_xml = utils.xml.load_from_reader(reader, 'news')
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


class SamuraiTelops(BaseTypeLoadable):
    entries: List[str]

    def _read(self, reader, config):
        telops_xml = utils.xml.load_from_reader(reader, 'telops')
        utils.xml.validate_schema(telops_xml, {'telop': None}, True)
        self.entries = [el.text for el in getattr(telops_xml, 'telop', [])]
