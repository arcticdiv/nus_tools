import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Type, Tuple

from . import common, movie, title_list
from .._base import BaseTypeLoadable, XmlBaseType, IDName
from ... import utils, ids


#####
# /title/<id>
#####

@dataclass(frozen=True)
class SamuraiTitleStars(common.SamuraiStars):
    @classmethod
    def _get_schema(cls):
        schema, _ = super()._get_schema()
        return {**schema, 'conditional_ratings': {'conditional_rating': {'score': None, 'votes': None}}}, True

    @classmethod
    def _parse_internal(cls, xml):
        # TODO: conditional_ratings unhandled
        return super()._parse_internal(xml)


@dataclass(frozen=True)
class SamuraiTitleFeature(XmlBaseType):
    required: bool
    type: int
    id: str
    name: str

    @classmethod
    def _get_schema(cls):
        return {'id': None, 'name': None, 'icons': {'icon': None}, 'description': None}, True

    @classmethod
    def _parse_internal(cls, xml):
        # TODO: icons, description unhandled
        return {
            'required': utils.misc.get_bool(xml.get('required')),
            'type': int(xml.get('type')),
            'id': xml.id.text,
            'name': xml.name.text
        }


@dataclass
class SamuraiTitleLanguage:
    iso_code: str
    name: str


@dataclass(frozen=True)
class SamuraiTitleController:
    required: bool
    type: int
    id: str
    name: str


@dataclass(frozen=True)
class SamuraiTitlePlayStyle:
    type: str
    controllers: List[SamuraiTitleController]
    features: List[SamuraiTitleFeature]


@dataclass(frozen=True)
class SamuraiTitlePreferenceTarget:
    everyone: int
    gamers: int


@dataclass(frozen=True)
class SamuraiTitlePreferenceStyle:
    casual: int
    intense: int


@dataclass(frozen=True)
class SamuraiTitlePreference:
    target_player: SamuraiTitlePreferenceTarget
    play_style: SamuraiTitlePreferenceStyle


@dataclass(frozen=True)
class SamuraiTitleWebsite:
    name: str
    url: str
    official: bool


@dataclass(frozen=True)
class SamuraiTitleLinkedDemo:
    content_id: ids.ContentID
    name: str
    icon_url: Optional[str]


@dataclass(frozen=True)
class SamuraiTitleScreenshot(common.SamuraiScreenshot):
    thumbnail_url: Optional[common.SamuraiScreenshotUrl] = None

    @classmethod
    def _get_schema(cls):
        schema, _ = super()._get_schema()
        return {**schema, 'thumbnail_url': None}, True

    @classmethod
    def _parse_internal(cls, xml):
        return {
            **super()._parse_internal(xml),
            'thumbnail_url': common.SamuraiScreenshotUrl._parse(xml.thumbnail_url) if hasattr(xml, 'thumbnail_url') else None
        }


@dataclass(frozen=True)
class _SamuraiTitleBaseMixin(title_list._SamuraiListTitleBaseMixin):
    is_public: bool
    formal_name: str
    genres: List[IDName]
    keywords: List[str]
    has_ticket: bool
    sales_download_code: bool
    sales_download_card: bool

    @classmethod
    def _try_parse_value(cls, vals: utils.dicts.dotdict, child, tag, text, custom_types: Dict[str, Type]) -> bool:
        if 'is_public' not in vals:
            xml = child.getparent()
            vals.is_public = utils.misc.get_bool(xml.get('public'))

        if tag == 'formal_name':
            vals.formal_name = text
        elif tag == 'genres':
            vals.genres = []
            for genre in child.genre:
                utils.xml.validate_schema(genre, {'name': None}, False)
                vals.genres.append(IDName(genre.get('id'), genre.name.text))
        elif tag == 'keywords':
            vals.keywords = [keyword.text for keyword in getattr(child, 'keyword', [])]
        elif tag == 'ticket_available':
            vals.has_ticket = utils.misc.get_bool(text)
        elif tag == 'download_code_sales':
            vals.sales_download_code = utils.misc.get_bool(text)
        elif tag == 'download_card_sales':
            utils.xml.validate_schema(child, None, False)
            vals.sales_download_card = utils.misc.get_bool(child.get('available'))
        else:
            return super()._try_parse_value(vals, child, tag, text, custom_types)
        return True


@dataclass(frozen=True)
class _SamuraiTitleOptionalMixin(title_list._SamuraiListTitleOptionalMixin[common.SamuraiRatingDetailed, SamuraiTitleStars]):
    sales_web: Optional[bool] = None
    top_image_type: Optional[str] = None
    top_image_url: Optional[str] = None
    description: Optional[str] = None
    price_description: Optional[str] = None
    features: Optional[List[SamuraiTitleFeature]] = None
    play_styles: Optional[List[SamuraiTitlePlayStyle]] = None
    languages: Optional[List[SamuraiTitleLanguage]] = None
    num_players: Optional[Tuple[int, int]] = None
    num_players_raw: Optional[str] = None
    disclaimer: Optional[str] = None
    copyright: Optional[str] = None
    screenshots: Optional[List[common.SamuraiScreenshot]] = None
    preferences: Optional[SamuraiTitlePreference] = None
    websites: Optional[List[SamuraiTitleWebsite]] = None
    movies: Optional[List[movie.SamuraiMovieElement]] = None
    demos: Optional[List[SamuraiTitleLinkedDemo]] = None
    peripheral_description: Optional[str] = None
    network_feature_description: Optional[str] = None
    size: Optional[int] = None

    @classmethod
    def _try_parse_value(cls, vals: utils.dicts.dotdict, child, tag, text, custom_types: Dict[str, Type]) -> bool:
        if tag == 'web_sales':
            vals.sales_web = utils.misc.get_bool(text)
        elif tag == 'top_image':
            utils.xml.validate_schema(child, {'type': None, 'url': None}, False)
            vals.top_image_type = child.type.text
            vals.top_image_url = child.url.text
        elif tag == 'description':
            vals.description = text
        elif tag == 'price_description':
            vals.price_description = text
        elif tag == 'features':
            vals.features = [SamuraiTitleFeature._parse(feature) for feature in child.feature]
        elif tag == 'play_styles':
            utils.xml.validate_schema(child, {'play_style': {'controllers': {'controller': {'id': None, 'name': None}}, 'features': {'feature': SamuraiTitleFeature._get_schema()[0]}}}, True)
            vals.play_styles = []
            for play_style in child.play_style:
                controllers = [
                    SamuraiTitleController(
                        utils.misc.get_bool(controller.get('required')),
                        int(controller.get('type')),
                        controller.id.text,
                        controller.name.text
                    )
                    for controller in play_style.controllers.controller
                ]
                if hasattr(play_style, 'features'):
                    features = [SamuraiTitleFeature._parse(feature) for feature in play_style.features.feature]
                else:
                    features = []
                vals.play_styles.append(SamuraiTitlePlayStyle(play_style.get('type'), controllers, features))
        elif tag == 'languages':
            vals.languages = []
            for language in child.language:
                utils.xml.validate_schema(language, {'iso_code': None, 'name': None}, False)
                vals.languages.append(SamuraiTitleLanguage(language.iso_code.text, language.name.text))
        elif tag == 'number_of_players':
            cleaned_text = text.split('\n', 2)[0]  # sometimes this field contains additional text in a second line, discard it for now
            matches = re.search(r'^(\d+)(?:\s*-\s*(\d+))?(?:\s+players?)?', cleaned_text)
            if matches:
                vals.num_players = (int(matches[1]), int(matches[2] or matches[1]))
            elif cleaned_text.startswith('*'):  # disclaimer instead of specific player numbers (example: 50010000037675)
                vals.num_players = None
            else:
                raise RuntimeError(f'Could not parse player details: {cleaned_text}')
            vals.num_players_raw = text
        elif tag == 'disclaimer':
            vals.disclaimer = text
        elif tag == 'copyright':
            utils.xml.validate_schema(child, {'text': None}, False)
            vals.copyright = child.find('text').text
        elif tag == 'screenshots':
            vals.screenshots = [SamuraiTitleScreenshot._parse(screenshot) for screenshot in child.screenshot]
        elif tag == 'preference':
            target = child.find('target_player')
            style = child.find('play_style')
            vals.preferences = SamuraiTitlePreference(
                SamuraiTitlePreferenceTarget(int(target.everyone.text), int(target.gamers.text)),
                SamuraiTitlePreferenceStyle(int(style.casual.text), int(style.intense.text))
            )
        elif tag == 'web_sites':
            vals.websites = []
            for website in child.web_site:
                utils.xml.validate_schema(website, {'name': None, 'url': None, 'official': None}, False)
                vals.websites.append(SamuraiTitleWebsite(
                    website.name.text,
                    website.url.text,
                    utils.misc.get_bool(website.official.text)
                ))
        elif tag == 'movies':
            vals.movies = [movie.SamuraiMovieElement._parse(m) for m in child.movie]
        elif tag == 'demo_titles':
            vals.demos = [
                SamuraiTitleLinkedDemo(
                    ids.ContentID(demo.get('id')),
                    demo.name.text,
                    utils.xml.get_text(demo, 'icon_url')
                )
                for demo in child.demo_title
            ]
        elif tag == 'peripheral_description':
            vals.peripheral_description = text
        elif tag == 'network_feature_description':
            vals.network_feature_description = text
        elif tag == 'data_size':
            vals.size = int(text)
        else:
            return super()._try_parse_value(vals, child, tag, text, custom_types)
        return True


# TODO: DRY (title.py, movie.py)
@dataclass(frozen=True)
class SamuraiTitleElement(_SamuraiTitleOptionalMixin, _SamuraiTitleBaseMixin):
    @classmethod
    def _parse(cls, xml) -> 'SamuraiTitleElement':
        vals = utils.dicts.dotdict()

        for child, tag, text in utils.xml.iter_children(xml):
            if _SamuraiTitleBaseMixin._try_parse_value(vals, child, tag, text, {}):
                pass
            elif _SamuraiTitleOptionalMixin._try_parse_value(
                vals, child, tag, text,
                {
                    'rating_info': common.SamuraiRatingDetailed,
                    'rating_stars': SamuraiTitleStars
                }
            ):
                pass
            else:
                raise ValueError(f'unknown tag: {tag}')

        return cls(**vals)


class SamuraiTitle(BaseTypeLoadable):
    title: SamuraiTitleElement

    def _read(self, reader, config):
        title_xml = utils.xml.load_from_reader(reader, 'title')
        self.title = SamuraiTitleElement._parse(title_xml)
