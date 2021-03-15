from dataclasses import dataclass
from typing import Dict, Type, Optional

from . import common, movie_list
from .._base import BaseType
from ... import reqdata, sources, utils


@dataclass(frozen=True)
class _SamuraiMovieBaseMixin(movie_list._SamuraiListMovieBaseMixin):
    @classmethod
    def _try_parse_value(cls, vals: utils.dotdict, child, tag, text, custom_types: Dict[str, Type]) -> bool:
        return super()._try_parse_value(vals, child, tag, text, custom_types)


@dataclass(frozen=True)
class _SamuraiMovieOptionalMixin(movie_list._SamuraiListMovieOptionalMixin[common.SamuraiRatingDetailed]):
    rating_info_alternate_image_url: Optional[str] = None

    @classmethod
    def _try_parse_value(cls, vals: utils.dotdict, child, tag, text, custom_types: Dict[str, Type]) -> bool:
        if tag == 'alternate_rating_image_url':
            vals.rating_info_alternate_image_url = text
        else:
            return super()._try_parse_value(vals, child, tag, text, custom_types)
        return True


@dataclass(frozen=True)
class SamuraiMovieElement(_SamuraiMovieOptionalMixin, _SamuraiMovieBaseMixin):
    @classmethod
    def _parse(cls, xml) -> 'SamuraiMovieElement':
        vals = utils.dotdict()

        for child, tag, text in utils.xml.iter_children(xml):
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


class SamuraiMovie(BaseType['sources.Samurai']):
    movie: SamuraiMovieElement

    def __init__(self, source: 'sources.Samurai', content_id: str):
        super().__init__(
            source,
            reqdata.ReqData(path=f'movie/{content_id}')
        )

    def _read(self, iterator):
        data = iterator.read_all()
        xml = utils.xml.read_object(data)
        assert len(xml.getchildren()) == 1
        movie = xml.movie

        self.movie = SamuraiMovieElement._parse(movie)
