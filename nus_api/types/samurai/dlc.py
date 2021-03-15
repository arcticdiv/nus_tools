import abc
from dataclasses import dataclass
from typing import List, Optional, Generic, TypeVar

from . import common
from .._base import BaseType
from ... import reqdata, sources, utils


#####
# /title/<id>/aocs
#####


_TDlc = TypeVar('_TDlc')


class _SamuraiDlcs(Generic[_TDlc], BaseType['sources.Samurai']):
    dlcs: List[_TDlc]

    def __init__(self, source: 'sources.Samurai', content_id: str):
        super().__init__(
            source,
            reqdata.ReqData(path=f'title/{content_id}/aocs', params={'limit': 200})  # assuming a maximum of 200 DLCs per title, seems reasonable
        )

    def _read(self, iterator):
        data = iterator.read_all()
        xml = utils.xml.read_object(data)
        assert len(xml.getchildren()) == 1
        title = xml.title

        self._read_dlcs(title)

    @abc.abstractmethod
    def _read_dlcs(self, title):
        pass


#####
# WiiU
#####

@dataclass(frozen=True)
class SamuraiDlcContentIndexes:
    variation: str
    indexes: List[int]


@dataclass(frozen=True)
class SamuraiDlcWiiU:
    is_new: bool
    content_id: str
    name: str
    icon_url: str
    content_indexes: SamuraiDlcContentIndexes
    description: str
    allow_overlap: bool  # not sure about the type here, value is mostly 0
    release_date: Optional[str] = None
    screenshots: Optional[List[common.SamuraiScreenshot]] = None
    disclaimer: Optional[str] = None
    promotion_image_urls: Optional[List[str]] = None
    promotion_video_url: Optional[str] = None

    @classmethod
    def _parse(cls, xml) -> 'SamuraiDlcWiiU':
        vals = utils.dotdict()
        vals.is_new = utils.get_bool(xml.get('new'))
        vals.content_id = xml.get('id')
        assert vals.content_id

        for child, tag, text in utils.xml.iter_children(xml):
            if tag == 'name':
                vals.name = text
            elif tag == 'item_new_since':
                vals.release_date = text
            elif tag == 'icon_url':
                vals.icon_url = text
            elif tag == 'screenshots':
                vals.screenshots = [common.SamuraiScreenshot._parse(screenshot) for screenshot in child.screenshot]
            elif tag == 'promotion_images':
                vals.promotion_image_urls = []
                for image in child.promotion_image:
                    assert set(image.attrib.keys()) == {'index', 'url'}
                    vals.promotion_image_urls.append(image.get('url'))
            elif tag == 'promotion_movie_url':
                vals.promotion_video_url = text
            elif tag == 'content_indexes':
                utils.xml.validate_schema(child, {'content_index': None}, False)
                vals.content_indexes = SamuraiDlcContentIndexes(
                    child.get('variation'),
                    [int(i) for i in child.content_index]
                )
            elif tag == 'description':
                vals.description = text
            elif tag == 'disclaimer':
                vals.disclaimer = text
            elif tag == 'allow_overlap':
                vals.allow_overlap = utils.get_bool(text)
            else:
                raise ValueError(f'unknown tag: {tag}')

        return cls(**vals)


class SamuraiDlcsWiiU(_SamuraiDlcs[SamuraiDlcWiiU]):
    name: str
    banner_url: Optional[str]
    description: Optional[str]

    def _read_dlcs(self, title):
        assert utils.xml.get_child_tags(title) <= {'name', 'aocs_banner_url', 'aocs_description', 'aocs'}
        self.name = title.name.text
        self.banner_url = utils.xml.get_text(title, 'aocs_banner_url')
        self.description = utils.xml.get_text(title, 'description')

        assert int(title.aocs.get('length')) == int(title.aocs.get('total'))  # sanity check, results could technically be paginated, but there's probably no title with >200 DLCs
        self.dlcs = [SamuraiDlcWiiU._parse(dlc) for dlc in title.aocs.aoc]


#####
# 3DS
#####

@dataclass
class SamuraiDlc3DS:
    name: str
    price: common.SamuraiPrice

    @classmethod
    def _parse(cls, xml) -> 'SamuraiDlc3DS':
        vals = utils.dotdict()

        for child, tag, text in utils.xml.iter_children(xml):
            if tag == 'name':
                vals.name = text
            elif tag == 'price':
                utils.xml.validate_schema(child, {'regular_price': {'amount': None, 'currency': None}}, False)
                vals.price = common.SamuraiPrice(
                    float(child.regular_price.amount),
                    child.regular_price.currency
                )
            else:
                raise ValueError(f'unknown tag: {tag}')

        return cls(**vals)


class SamuraiDlcs3DS(_SamuraiDlcs[SamuraiDlc3DS]):
    def _read_dlcs(self, title):
        # some titles have `aoc_available = True`, but the aoc XML doesn't contain anything :/
        assert utils.xml.get_child_tags(title) <= {'aocs'}
        self.dlcs = [SamuraiDlc3DS._parse(dlc) for dlc in title.aocs.aoc] if hasattr(title, 'aocs') else []
