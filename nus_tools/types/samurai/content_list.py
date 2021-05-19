from typing import List

from . import movie_list, title_list
from .common import SamuraiListBaseType


class SamuraiContentsList(SamuraiListBaseType):
    titles: List[title_list.SamuraiListTitle]
    movies: List[movie_list.SamuraiListMovie]

    def _read_list(self, xml):
        assert xml.tag == 'contents'
        self.titles = []
        self.movies = []
        for content in xml.content:
            if hasattr(content, 'title'):
                self.titles.append(title_list.SamuraiListTitle._parse(content.title))
            elif hasattr(content, 'movie'):
                self.movies.append(movie_list.SamuraiListMovie._parse(content.movie))
            else:
                raise ValueError(content.getchildren()[0].tag)
