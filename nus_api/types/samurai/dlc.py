import abc
from dataclasses import dataclass
from typing import Dict, List, Optional, Generic, TypeVar

from . import common
from .._base import BaseTypeLoadable
from ... import reqdata, sources, utils, ids


# welcome to inheritance hell
# graph of the main classes (because this file might be somewhat difficult to understand initially):
#
#                                       BaseTypeLoadable
#                                              |
#                                      SamuraiDlcsBase[T]
#                                     /                  \
#                  T: SamuraiDlcWiiU /                    \
#                                   /                      \
#                     SamuraiDlcsWiiUBase              SamuraiTitleDlcsBase[T]
#                    /                   \            /                       \
#                   /                     \          / T: SamuraiDlcWiiU       \ T: SamuraiDlc3DS
#                  /                       \        /                           \
#          SamuraiDlcsWiiU            SamuraiTitleDlcsWiiU              SamuraiTitleDlcs3DS


_TDlc = TypeVar('_TDlc')


class SamuraiDlcsBase(Generic[_TDlc], BaseTypeLoadable['sources.Samurai']):
    dlcs: List[_TDlc]


class SamuraiTitleDlcsBase(SamuraiDlcsBase[_TDlc]):
    def __init__(self, source: 'sources.Samurai', content_id: ids.TContentIDInput):
        super().__init__(
            source,
            reqdata.ReqData(path=f'title/{ids.ContentID.get_str(content_id)}/aocs', params={'limit': 200})  # assuming a maximum of 200 DLCs per title, seems reasonable
        )

    def _read(self, reader):
        title_xml = utils.xml.load_from_reader(reader, 'title')
        self._read_title(title_xml)

    @abc.abstractmethod
    def _read_title(self, title):
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
    content_id: ids.ContentID
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
        vals = utils.dicts.dotdict()
        vals.is_new = utils.misc.get_bool(xml.get('new'))
        vals.content_id = ids.ContentID(xml.get('id'))

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
                    [int(i.text) for i in child.content_index]
                )
            elif tag == 'description':
                vals.description = text
            elif tag == 'disclaimer':
                vals.disclaimer = text
            elif tag == 'allow_overlap':
                vals.allow_overlap = utils.misc.get_bool(text)
            else:
                raise ValueError(f'unknown tag: {tag}')

        return cls(**vals)


class SamuraiDlcsWiiUBase(SamuraiDlcsBase[SamuraiDlcWiiU]):
    def _read_dlcs(self, aocs):
        assert int(aocs.get('length')) == int(aocs.get('total'))  # sanity check, results could technically be paginated, but there's probably no title with >200 DLCs
        self.dlcs = [SamuraiDlcWiiU._parse(dlc) for dlc in aocs.aoc] if hasattr(aocs, 'aoc') else []


#####
# /aocs
#####

class SamuraiDlcsWiiU(SamuraiDlcsWiiUBase):
    def __init__(self, source: 'sources.Samurai', dlc_ids: List[ids.TContentIDInput]):
        super().__init__(
            source,
            reqdata.ReqData(
                path='aocs',
                params={'aoc[]': ','.join(ids.ContentID.get_str(i) for i in dlc_ids)}
            )
        )

    def _read(self, reader):
        aocs = utils.xml.load_from_reader(reader, 'aocs')
        self._read_dlcs(aocs)


#####
# /aocs/size
#####

class SamuraiDlcSizes(BaseTypeLoadable['sources.Samurai']):
    sizes: Dict[ids.ContentID, int]

    def __init__(self, source: 'sources.Samurai', dlc_ids: List[ids.TContentIDInput]):
        super().__init__(
            source,
            reqdata.ReqData(
                path='aocs/size',
                params={'aoc[]': ','.join(ids.ContentID.get_str(i) for i in dlc_ids)}
            )
        )

    def _read(self, reader):
        aocs = utils.xml.load_from_reader(reader, 'aocs')
        utils.xml.validate_schema(aocs, {'aoc': {'data_size': None}}, False)

        self.sizes = {ids.ContentID(aoc.get('id')): int(aoc.data_size.text) for aoc in aocs.aoc}


#####
# /aocs/prices
#####

@dataclass(frozen=True)
class SamuraiDlcPrice:
    eshop_status: str
    price_id: str
    price: common.SamuraiPrice


class SamuraiDlcPrices(BaseTypeLoadable['sources.Samurai']):
    prices: Dict[ids.ContentID, SamuraiDlcPrice]

    def __init__(self, source: 'sources.Samurai', dlc_ids: List[ids.TContentIDInput]):
        super().__init__(
            source,
            reqdata.ReqData(
                path='aocs/prices',
                params={'aoc[]': ','.join(ids.ContentID.get_str(i) for i in dlc_ids)}
            )
        )

    def _read(self, reader):
        prices = utils.xml.load_from_reader(reader, 'online_prices')
        utils.xml.validate_schema(prices, {'online_price': {'aoc_id': None, 'eshop_sales_status': None, 'price': {'regular_price': {'amount': None, 'currency': None, 'raw_value': None}}}}, False)

        self.prices = {}
        for price in prices.online_price:
            assert len(price.price.getchildren()) == 1
            regular_price = price.price.regular_price
            self.prices[ids.ContentID(price.aoc_id.text)] = SamuraiDlcPrice(
                price.eshop_sales_status.text,
                regular_price.get('id'),
                common.SamuraiPrice(
                    float(regular_price.raw_value.text),
                    regular_price.currency.text
                )
            )


#####
# /title/<id>/aocs
#####

class SamuraiTitleDlcsWiiU(SamuraiTitleDlcsBase[SamuraiDlcWiiU], SamuraiDlcsWiiUBase):
    name: str
    banner_url: Optional[str]
    description: Optional[str]

    def _read_title(self, title):
        assert utils.xml.get_child_tags(title) <= {'name', 'aocs_banner_url', 'aocs_description', 'aocs'}
        self.name = title.name.text
        self.banner_url = utils.xml.get_text(title, 'aocs_banner_url')
        self.description = utils.xml.get_text(title, 'description')

        self._read_dlcs(title.aocs)


#####
# 3DS
#####

@dataclass
class SamuraiDlc3DS:
    name: str
    price: common.SamuraiPrice

    @classmethod
    def _parse(cls, xml) -> 'SamuraiDlc3DS':
        vals = utils.dicts.dotdict()

        for child, tag, text in utils.xml.iter_children(xml):
            if tag == 'name':
                vals.name = text
            elif tag == 'price':
                utils.xml.validate_schema(child, {'regular_price': {'amount': None, 'currency': None}}, False)
                vals.price = common.SamuraiPrice(
                    float(child.regular_price.amount.text),
                    child.regular_price.currency.text
                )
            else:
                raise ValueError(f'unknown tag: {tag}')

        return cls(**vals)


#####
# /title/<id>/aocs
#####

class SamuraiTitleDlcs3DS(SamuraiTitleDlcsBase[SamuraiDlc3DS]):
    def _read_title(self, title):
        # some titles have `aoc_available = True`, but the aoc XML doesn't contain anything :/
        assert utils.xml.get_child_tags(title) <= {'aocs'}
        self.dlcs = [SamuraiDlc3DS._parse(dlc) for dlc in title.aocs.aoc] if hasattr(title, 'aocs') else []
