from dataclasses import dataclass
from typing import Dict, List, Optional

from .._base import XmlBaseType


@dataclass
class IDName:
    id: str
    name: str


@dataclass(frozen=True)
class SamuraiRating(XmlBaseType):
    system: IDName
    id: str
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
        # TODO: rating.icons unhandled
        return {
            'system': IDName(xml.rating_system.get('id'), xml.rating_system.name.text),
            'id': xml.rating.get('id'),
            'name': xml.rating.name.text,
            'age': xml.rating.age.text
        }


@dataclass(frozen=True)
class SamuraiRatingDetailed(SamuraiRating):
    descriptors: List[str]

    @classmethod
    def _get_schema(cls):
        schema, _ = super()._get_schema()
        return {**schema, 'descriptors': {'descriptor': {'name': None}}}, True

    @classmethod
    def _parse_internal(cls, xml):
        return {
            **super()._parse_internal(xml),
            'descriptors': [d.name.text for d in xml.descriptors.descriptor] if hasattr(xml, 'descriptors') and hasattr(xml.descriptors, 'descriptor') else []
        }


@dataclass(frozen=True)
class SamuraiPlatform(XmlBaseType):
    id: str
    device: str
    category: str
    name: str

    @classmethod
    def _get_schema(cls):
        return {'name': None}, False

    @classmethod
    def _parse_internal(cls, xml):
        return {
            'id': xml.get('id'),
            'device': xml.get('device'),
            'category': xml.get('category'),
            'name': xml.name.text
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
    amount: float
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
