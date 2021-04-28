import lxml.objectify
from dataclasses import dataclass
from typing import List, Optional, Type, TypeVar, Generic
from typing_extensions import TypedDict

import reqcli.utils.xml as xmlutils

from . import common
from ... import utils, ids


CustomTypes = TypedDict(
    'CustomTypes',
    {
        'rating_info': Type[common.SamuraiRating]
    },
    total=False
)


@dataclass(frozen=True)
class SamuraiMovieFile:
    quality: str
    format: str
    url: str
    width: int
    height: int
    dimension: str
    seconds: int

    @classmethod
    def _parse(cls, xml: lxml.objectify.ObjectifiedElement) -> 'SamuraiMovieFile':
        vals = utils.misc.dotdict()
        vals.quality = xml.get('quality')

        for child, tag, text in xmlutils.iter_children(xml):
            if tag == 'format':
                vals.format = text
            elif tag == 'movie_url':
                vals.url = text
            elif tag == 'width':
                vals.width = int(text)
            elif tag == 'height':
                vals.height = int(text)
            elif tag == 'dimension':
                vals.dimension = text
            elif tag == 'play_time_sec':
                vals.seconds = int(text)
            else:
                raise ValueError(f'unknown tag: {tag}')

        return cls(**vals)


@dataclass(frozen=True)
class SamuraiMovieLinkedTitle:
    id: ids.ContentID
    name: str
    icon_url: Optional[str]
    banner_url: Optional[str]


@dataclass(frozen=True)
class _SamuraiListMovieBaseMixin:
    is_new: bool
    content_id: ids.ContentID
    name: str
    files: List[SamuraiMovieFile]

    @classmethod
    def _try_parse_value(cls, vals: utils.misc.dotdict, child: lxml.objectify.ObjectifiedElement, tag: str, text: str, custom_types: CustomTypes) -> bool:
        if 'is_new' not in vals:
            xml = child.getparent()
            vals.is_new = utils.misc.get_bool(xml.get('new'))
            vals.content_id = ids.ContentID(xml.get('id'))

        if tag == 'name':
            vals.name = text
        elif tag == 'files':
            vals.files = [SamuraiMovieFile._parse(el) for el in getattr(child, 'file', [])]
        else:
            return False
        return True


_TRating = TypeVar('_TRating', bound=common.SamuraiRating)


@dataclass(frozen=True)
class _SamuraiListMovieOptionalMixin(Generic[_TRating]):
    icon_url: Optional[str] = None
    banner_url: Optional[str] = None
    title: Optional[SamuraiMovieLinkedTitle] = None
    rating_info: Optional[_TRating] = None

    @classmethod
    def _try_parse_value(cls, vals: utils.misc.dotdict, child: lxml.objectify.ObjectifiedElement, tag: str, text: str, custom_types: CustomTypes) -> bool:
        if tag == 'icon_url':
            vals.icon_url = text
        elif tag == 'banner_url':
            vals.banner_url = text
        elif tag == 'title':
            xmlutils.validate_schema(child, {'name': None, 'icon_url': None, 'banner_url': None}, True)
            vals.title = SamuraiMovieLinkedTitle(
                ids.ContentID(child.get('id')),
                child.name.text,
                xmlutils.get_text(child, 'icon_url'),
                xmlutils.get_text(child, 'banner_url')
            )
        elif tag == 'rating_info':
            vals.rating_info = custom_types['rating_info']._parse(child)
        else:
            return False
        return True


@dataclass(frozen=True)
class SamuraiListMovie(_SamuraiListMovieOptionalMixin[common.SamuraiRating], _SamuraiListMovieBaseMixin):
    @classmethod
    def _parse(cls, xml: lxml.objectify.ObjectifiedElement) -> 'SamuraiListMovie':
        vals = utils.misc.dotdict()

        for child, tag, text in xmlutils.iter_children(xml):
            if _SamuraiListMovieBaseMixin._try_parse_value(vals, child, tag, text, {}):
                pass
            elif _SamuraiListMovieOptionalMixin._try_parse_value(
                vals, child, tag, text,
                {
                    'rating_info': common.SamuraiRating
                }
            ):
                pass
            else:
                raise ValueError(f'unknown tag: {tag}')

        return cls(**vals)


class SamuraiMoviesList(common.SamuraiListBaseType):
    movies: List[SamuraiListMovie]

    def _read_list(self, xml):
        assert xml.tag == 'contents'
        self.movies = [SamuraiListMovie._parse(content.movie) for content in xml.content]
