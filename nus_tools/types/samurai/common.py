import abc
from dataclasses import dataclass
from typing import Dict, List, Optional

import reqcli.utils.xml as xmlutils
from reqcli.type import BaseTypeLoadable, XmlBaseType


class SamuraiListBaseType(BaseTypeLoadable, abc.ABC):
    length: int
    offset: int
    total: int

    def _read(self, reader, config):
        el = xmlutils.load_root(reader)
        self.length = int(el.get('length'))
        self.offset = int(el.get('offset'))
        self.total = int(el.get('total'))

        self._read_list(el)

    @abc.abstractmethod
    def _read_list(self, xml):
        pass


@dataclass(frozen=True)
class IDName:
    id: int
    name: str


@dataclass(frozen=True)
class SamuraiIcon:
    url: str
    type: str

    @classmethod
    def _parse(cls, xml):
        assert set(xml.attrib.keys()) == {'url', 'type'}
        assert not xml.text
        return cls(
            xml.get('url'),
            xml.get('type')
        )


@dataclass(frozen=True)
class SamuraiRating(XmlBaseType):
    system: IDName
    id: int
    icons: List[SamuraiIcon]
    name: str
    age: str

    @classmethod
    def _get_schema(cls):
        return {
            'rating_system': {'name': None},
            'rating': {'icons': {'icon': None}, 'name': None, 'age': None}
        }, False

    @classmethod
    def _parse_internal(cls, xml):
        return {
            'system': IDName(int(xml.rating_system.get('id')), xml.rating_system.name.text),
            'id': int(xml.rating.get('id')),
            'icons': [SamuraiIcon._parse(icon) for icon in xml.rating.icons.icon],
            'name': xml.rating.name.text,
            'age': xml.rating.age.text
        }


@dataclass(frozen=True)
class SamuraiRatingDescriptor:
    name: Optional[str] = None
    icons: Optional[List[SamuraiIcon]] = None


@dataclass(frozen=True)
class SamuraiRatingDetailed(SamuraiRating):
    descriptors: List[SamuraiRatingDescriptor]

    @classmethod
    def _get_schema(cls):
        schema, _ = super()._get_schema()
        return {**schema, 'descriptors': {'descriptor': {'name': None, 'icons': {'icon': None}}}}, True

    @classmethod
    def _parse_internal(cls, xml):
        descriptors = []
        if hasattr(xml, 'descriptors') and hasattr(xml.descriptors, 'descriptor'):
            for d in xml.descriptors.descriptor:
                descriptors.append(SamuraiRatingDescriptor(
                    xmlutils.get_text(d, 'name'),
                    [SamuraiIcon._parse(icon) for icon in d.icons.icon] if hasattr(d, 'icons') else None
                ))

        return {
            **super()._parse_internal(xml),
            'descriptors': descriptors
        }


@dataclass(frozen=True)
class SamuraiPlatform(XmlBaseType):
    id: int
    device: str
    category: str
    name: str
    icon_url: Optional[str]

    @classmethod
    def _get_schema(cls):
        return {'name': None, 'icon_url': None}, True

    @classmethod
    def _parse_internal(cls, xml):
        return {
            'id': int(xml.get('id')),
            'device': xml.get('device'),
            'category': xml.get('category'),
            'name': xml.name.text,
            'icon_url': xmlutils.get_text(xml, 'icon_url')
        }


@dataclass(frozen=True)
class SamuraiStars(XmlBaseType):
    score: float
    total_votes: int
    stars: Dict[int, int]

    @classmethod
    def _get_schema(cls):
        return {'score': None, 'votes': None, **{f'star{i}': None for i in range(1, 6)}}, False

    @classmethod
    def _parse_internal(cls, xml):
        return {
            'score': float(xml.score.text),
            'total_votes': int(xml.votes.text),
            'stars': {i: int(xml[f'star{i}'].text) for i in range(1, 6)}
        }


@dataclass(frozen=True)
class SamuraiPrice:
    amount: Optional[float]
    currency: str


@dataclass(frozen=True)
class SamuraiScreenshotUrl:
    url: str
    type: Optional[str] = None
    index: Optional[int] = None

    @classmethod
    def _parse(cls, xml):
        assert set(xml.attrib.keys()) <= {'type', 'index'}
        return cls(
            xml.text,
            xml.get('type'),
            int(xml.get('index')) if 'index' in xml.attrib else None
        )


@dataclass(frozen=True)
class SamuraiScreenshot(XmlBaseType):
    image_urls: List[SamuraiScreenshotUrl]

    @classmethod
    def _get_schema(cls):
        return {'image_url': None}, False

    @classmethod
    def _parse_internal(cls, xml):
        return {
            'image_urls': [SamuraiScreenshotUrl._parse(image_url) for image_url in xml.image_url]
        }
