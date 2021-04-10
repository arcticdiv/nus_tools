from typing import List

from . import movie, title_list
from ._base import SamuraiListBaseType


class SamuraiContentsList(SamuraiListBaseType):
    titles: List[title_list.SamuraiListTitle]
    movies: List[movie.SamuraiMovieElement]

    def _read_list(self, xml):
        assert xml.tag == 'contents'
        self.titles = []
        self.movies = []
        for content in xml.content:
            if hasattr(content, 'title'):
                self.titles.append(title_list.SamuraiListTitle._parse(content.title))
            elif hasattr(content, 'movie'):
                self.movies.append(movie.SamuraiMovieElement._parse(content.movie))
            else:
                raise ValueError(content.getchildren()[0].tag)
