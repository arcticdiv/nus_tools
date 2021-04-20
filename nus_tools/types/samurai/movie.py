import lxml.objectify
from dataclasses import dataclass
from typing import Optional

import reqcli.utils.xml as xmlutils
from reqcli.type import BaseTypeLoadable

from . import common, movie_list
from ... import utils


@dataclass(frozen=True)
class _SamuraiMovieBaseMixin(movie_list._SamuraiListMovieBaseMixin):
    @classmethod
    def _try_parse_value(cls, vals: utils.misc.dotdict, child: lxml.objectify.ObjectifiedElement, tag: str, text: str, custom_types: movie_list.CustomTypes) -> bool:
        return super()._try_parse_value(vals, child, tag, text, custom_types)


@dataclass(frozen=True)
class _SamuraiMovieOptionalMixin(movie_list._SamuraiListMovieOptionalMixin[common.SamuraiRatingDetailed]):
    rating_info_alternate_image_url: Optional[str] = None

    @classmethod
    def _try_parse_value(cls, vals: utils.misc.dotdict, child: lxml.objectify.ObjectifiedElement, tag: str, text: str, custom_types: movie_list.CustomTypes) -> bool:
        if tag == 'alternate_rating_image_url':
            vals.rating_info_alternate_image_url = text
        else:
            return super()._try_parse_value(vals, child, tag, text, custom_types)
        return True


@dataclass(frozen=True)
class SamuraiMovieElement(_SamuraiMovieOptionalMixin, _SamuraiMovieBaseMixin):
    @classmethod
    def _parse(cls, xml: lxml.objectify.ObjectifiedElement) -> 'SamuraiMovieElement':
        vals = utils.misc.dotdict()

        for child, tag, text in xmlutils.iter_children(xml):
            if _SamuraiMovieBaseMixin._try_parse_value(vals, child, tag, text, {}):
                pass
            elif _SamuraiMovieOptionalMixin._try_parse_value(
                vals, child, tag, text,
                {
                    'rating_info': common.SamuraiRatingDetailed
                }
            ):
                pass
            else:
                raise ValueError(f'unknown tag: {tag}')

        return cls(**vals)


class SamuraiMovie(BaseTypeLoadable):
    movie: SamuraiMovieElement

    def _read(self, reader, config):
        movie_xml = xmlutils.load_root(reader, 'movie')
        self.movie = SamuraiMovieElement._parse(movie_xml)
