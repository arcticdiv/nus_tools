import lxml.objectify
from dataclasses import dataclass
from typing import Generic, List, Optional, Type, TypeVar
from typing_extensions import TypedDict

import reqcli.utils.xml as xmlutils

from . import common
from ... import utils, ids


CustomTypes = TypedDict(
    'CustomTypes',
    {
        'rating_info': Type[common.SamuraiRating],
        'rating_stars': Type[common.SamuraiStars]
    },
    total=False
)


@dataclass(frozen=True)
class _SamuraiListTitleBaseMixin:
    is_new: bool
    content_id: ids.ContentID
    product_code: str
    name: str
    platform: common.SamuraiPlatform
    publisher: common.IDName
    genre: str
    sales_retail: bool
    sales_eshop: bool
    has_demo: bool
    # these values are sometimes false even though the title has aocs
    has_dlc__inaccurate: bool
    has_iap__inaccurate: bool

    @classmethod
    def _try_parse_value(cls, vals: utils.misc.dotdict, child: lxml.objectify.ObjectifiedElement, tag: str, text: str, custom_types: CustomTypes) -> bool:
        # kind of hacky, but it works
        if 'is_new' not in vals:
            xml = child.getparent()
            vals.is_new = utils.misc.get_bool(xml.get('new'))
            vals.content_id = ids.ContentID(xml.get('id'))

        if tag == 'product_code':
            vals.product_code = text
        elif tag == 'name':
            vals.name = text
        elif tag == 'platform':
            vals.platform = common.SamuraiPlatform._parse(child)
        elif tag == 'publisher':
            xmlutils.validate_schema(child, {'name': None}, False)
            vals.publisher = common.IDName(child.get('id'), child.name.text)
        elif tag == 'display_genre':
            vals.genre = text
        elif tag == 'retail_sales':
            vals.sales_retail = utils.misc.get_bool(text)
        elif tag == 'eshop_sales':
            vals.sales_eshop = utils.misc.get_bool(text)
        elif tag == 'demo_available':
            vals.has_demo = utils.misc.get_bool(text)
        elif tag == 'aoc_available':
            vals.has_dlc__inaccurate = utils.misc.get_bool(text)
        elif tag == 'in_app_purchase':
            vals.has_iap__inaccurate = utils.misc.get_bool(text)
        elif tag == 'release_date_on_original':
            pass  # unused
        elif tag == 'price_on_retail':
            pass  # unused
        elif tag == 'tentative_price_on_eshop':
            pass  # unused
        else:
            return False
        return True


_TRating = TypeVar('_TRating', bound=common.SamuraiRating)
_TStars = TypeVar('_TStars', bound=common.SamuraiStars)


@dataclass(frozen=True)
class _SamuraiListTitleOptionalMixin(Generic[_TRating, _TStars]):
    icon_url: Optional[str] = None
    banner_url: Optional[str] = None
    rating_info: Optional[_TRating] = None
    rating_stars: Optional[_TStars] = None
    release_date_eshop: Optional[str] = None
    release_date_retail: Optional[str] = None
    price_retail: Optional[common.SamuraiPrice] = None

    # have to specify generic parameters twice: in base class definition and in custom_types parameter;
    # classmethods don't have access to the generic parameters of their classes for some reason, see https://github.com/python/typing/issues/629
    @classmethod
    def _try_parse_value(cls, vals: utils.misc.dotdict, child: lxml.objectify.ObjectifiedElement, tag: str, text: str, custom_types: CustomTypes) -> bool:
        if tag == 'icon_url':
            vals.icon_url = text
        elif tag == 'banner_url':
            vals.banner_url = text
        elif tag == 'rating_info':
            vals.rating_info = custom_types['rating_info']._parse(child)
        elif tag == 'star_rating_info':
            vals.rating_stars = custom_types['rating_stars']._parse(child)
        elif tag == 'release_date_on_eshop':
            vals.release_date_eshop = text
        elif tag == 'release_date_on_retail':
            vals.release_date_retail = text
        elif tag == 'price_on_retail_detail':
            xmlutils.validate_schema(child, {'amount': None, 'currency': None, 'raw_value': None}, True)
            vals.price_retail = common.SamuraiPrice(
                float(child.raw_value.text) if 'TBD' not in child.amount.text else -1.0,
                child.currency
            )
        else:
            return False
        return True


@dataclass(frozen=True)
class SamuraiListTitle(_SamuraiListTitleOptionalMixin[common.SamuraiRating, common.SamuraiStars], _SamuraiListTitleBaseMixin):
    @classmethod
    def _parse(cls, xml: lxml.objectify.ObjectifiedElement) -> 'SamuraiListTitle':
        vals = utils.misc.dotdict()

        for child, tag, text in xmlutils.iter_children(xml):
            if _SamuraiListTitleBaseMixin._try_parse_value(vals, child, tag, text, {}):
                pass
            elif _SamuraiListTitleOptionalMixin._try_parse_value(
                vals, child, tag, text,
                {
                    'rating_info': common.SamuraiRating,
                    'rating_stars': common.SamuraiStars
                }
            ):
                pass
            else:
                raise ValueError(f'unknown tag: {tag}')

        return cls(**vals)


class SamuraiTitlesList(common.SamuraiListBaseType):
    titles: List[SamuraiListTitle]

    def _read_list(self, xml):
        assert xml.tag == 'contents'
        self.titles = [SamuraiListTitle._parse(content.title) for content in xml.content]
