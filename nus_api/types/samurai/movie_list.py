from dataclasses import dataclass
from typing import List, Optional, Dict, Type, TypeVar, Generic

from . import common
from ._base import SamuraiListBaseType
from ... import utils


#####
# /movies
#####


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
    def _parse(cls, xml) -> 'SamuraiMovieFile':
        vals = utils.dicts.dotdict()
        vals.quality = xml.get('quality')

        for child, tag, text in utils.xml.iter_children(xml):
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
    id: str
    name: str
    icon_url: Optional[str]
    banner_url: Optional[str]


@dataclass(frozen=True)
class _SamuraiListMovieBaseMixin:
    is_new: bool
    content_id: str
    name: str
    files: List[SamuraiMovieFile]

    @classmethod
    def _try_parse_value(cls, vals: utils.dicts.dotdict, child, tag, text, custom_types: Dict[str, Type]) -> bool:
        if 'is_new' not in vals:
            xml = child.getparent()
            vals.is_new = utils.misc.get_bool(xml.get('new'))
            vals.content_id = xml.get('id')
            assert vals.content_id

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
    def _try_parse_value(cls, vals: utils.dicts.dotdict, child, tag, text, custom_types: Dict[str, Type]) -> bool:
        if tag == 'icon_url':
            vals.icon_url = text
        elif tag == 'banner_url':
            vals.banner_url = text
        elif tag == 'title':
            utils.xml.validate_schema(child, {'name': None, 'icon_url': None, 'banner_url': None}, True)
            vals.title = SamuraiMovieLinkedTitle(
                child.get('id'),
                child.name.text,
                utils.xml.get_text(child, 'icon_url'),
                utils.xml.get_text(child, 'banner_url')
            )
        elif tag == 'rating_info':
            vals.rating_info = custom_types['rating_info']._parse(child)
        else:
            return False
        return True


@dataclass(frozen=True)
class SamuraiListMovie(_SamuraiListMovieOptionalMixin[common.SamuraiRating], _SamuraiListMovieBaseMixin):
    @classmethod
    def _parse(cls, xml) -> 'SamuraiListMovie':
        vals = utils.dicts.dotdict()

        for child, tag, text in utils.xml.iter_children(xml):
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


class SamuraiMoviesList(SamuraiListBaseType):
    movies: List[SamuraiListMovie]

    def _read_list(self, xml):
        assert xml.tag == 'contents'
        self.movies = [SamuraiListMovie._parse(content.movie) for content in xml.content]

    @classmethod
    def _get_req_path(cls) -> str:
        return 'movies'
