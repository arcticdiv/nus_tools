import re
import lxml.objectify
from dataclasses import dataclass
from typing import List, Optional, Tuple

import reqcli.utils.xml as xmlutils
from reqcli.type import BaseTypeLoadable, XmlBaseType

from . import common, movie_list, title_list
from ... import utils, ids


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
    id: int
    name: str
    icons: Optional[List[common.SamuraiIcon]]
    description: Optional[str]
    ext_info: Optional[str]

    @classmethod
    def _get_schema(cls):
        return {'id': None, 'name': None, 'icons': {'icon': None}, 'description': None, 'ext_info': None}, True

    @classmethod
    def _parse_internal(cls, xml):
        return {
            'required': utils.misc.get_bool(xml.get('required')),
            'type': int(xml.get('type')),
            'id': int(xml.id.text),
            'name': xml.name.text,
            'icons': [common.SamuraiIcon._parse(icon) for icon in xml.icons.icon] if hasattr(xml, 'icons') else None,
            'description': xmlutils.get_text(xml, 'description'),
            'ext_info': xmlutils.get_text(xml, 'ext_info')
        }


@dataclass
class SamuraiTitleLanguage:
    iso_code: str
    name: str


@dataclass(frozen=True)
class SamuraiTitleController:
    required: bool
    type: int
    id: int
    name: str
    icons: Optional[List[common.SamuraiIcon]]


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
class SamuraiSharedMovie(XmlBaseType):
    name: str
    url: str  # not a real url, at least not with `shared_site = 'youtube'` (in which case it's actually the video ID)
    official: bool
    shared_site: str

    @classmethod
    def _get_schema(cls):
        return {'name': None, 'url': None, 'official': None, 'shared_site': None}, False

    @classmethod
    def _parse_internal(cls, xml):
        return {
            'name': xml.name.text,
            'url': xml.url.text,
            'official': utils.misc.get_bool(xml.official.text),
            'shared_site': xml.shared_site.text
        }


@dataclass(frozen=True)
class SamuraiTitleNotice:
    type: str
    url: str
    display_name: str
    description: str


@dataclass(frozen=True)
class SamuraiDigitalManual:
    name: str
    url: str


@dataclass(frozen=True)
class SamuraiDownloadCardSales:
    available: bool
    image_url: Optional[str]


@dataclass(frozen=True)
class SamuraiTitleCopyright:
    text: str
    image_url: str


@dataclass(frozen=True)
class _SamuraiTitleBaseMixin(title_list._SamuraiListTitleBaseMixin):
    is_public: bool
    formal_name: str
    genres: List[common.IDName]
    keywords: List[str]
    has_ticket: bool
    sales_download_code: bool
    sales_download_card: SamuraiDownloadCardSales

    @classmethod
    def _try_parse_value(cls, vals: utils.misc.dotdict, child: lxml.objectify.ObjectifiedElement, tag: str, text: str, custom_types: title_list.CustomTypes) -> bool:
        if 'is_public' not in vals:
            xml = child.getparent()
            vals.is_public = utils.misc.get_bool(xml.get('public'))

        if tag == 'formal_name':
            vals.formal_name = text
        elif tag == 'genres':
            vals.genres = []
            for genre in child.genre:
                xmlutils.validate_schema(genre, {'name': None}, False)
                vals.genres.append(common.IDName(int(genre.get('id')), genre.name.text))
        elif tag == 'keywords':
            vals.keywords = [keyword.text for keyword in getattr(child, 'keyword', [])]
        elif tag == 'ticket_available':
            vals.has_ticket = utils.misc.get_bool(text)
        elif tag == 'download_code_sales':
            vals.sales_download_code = utils.misc.get_bool(text)
        elif tag == 'download_card_sales':
            xmlutils.validate_schema(child, {'image_url': None}, True)
            vals.sales_download_card = SamuraiDownloadCardSales(
                utils.misc.get_bool(child.get('available')),
                xmlutils.get_text(child, 'image_url')
            )
        else:
            return super()._try_parse_value(vals, child, tag, text, custom_types)
        return True


@dataclass(frozen=True)
class _SamuraiTitleOptionalMixin(title_list._SamuraiListTitleOptionalMixin[common.SamuraiRatingDetailed, SamuraiTitleStars]):
    package_url: Optional[str] = None
    hero_banner_url: Optional[str] = None
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
    copyright: Optional[SamuraiTitleCopyright] = None
    screenshots: Optional[List[common.SamuraiScreenshot]] = None
    main_images: Optional[List[common.SamuraiScreenshot]] = None
    preferences: Optional[SamuraiTitlePreference] = None
    websites: Optional[List[SamuraiTitleWebsite]] = None
    movies: Optional[List[movie_list.SamuraiListMovie]] = None
    demos: Optional[List[SamuraiTitleLinkedDemo]] = None
    peripheral_description: Optional[str] = None
    network_feature_description: Optional[str] = None
    spec_description: Optional[str] = None
    size: Optional[int] = None
    save_data_count: Optional[str] = None
    save_data_volume: Optional[str] = None
    catch_copy: Optional[str] = None
    shared_movies: Optional[List[SamuraiSharedMovie]] = None
    title_notices: Optional[List[SamuraiTitleNotice]] = None
    title_metas: Optional[List[Tuple[str, str]]] = None
    digital_manuals: Optional[List[SamuraiDigitalManual]] = None
    aoc_infos: Optional[str] = None

    @classmethod
    def _try_parse_value(cls, vals: utils.misc.dotdict, child: lxml.objectify.ObjectifiedElement, tag: str, text: str, custom_types: title_list.CustomTypes) -> bool:
        if tag == 'package_url':
            vals.package_url = text
        elif tag == 'hero_banner_url':
            vals.hero_banner_url = text
        elif tag == 'web_sales':
            vals.sales_web = utils.misc.get_bool(text)
        elif tag == 'top_image':
            xmlutils.validate_schema(child, {'type': None, 'url': None}, False)
            vals.top_image_type = child.type.text
            vals.top_image_url = child.url.text
        elif tag == 'description':
            vals.description = text
        elif tag == 'price_description':
            vals.price_description = text
        elif tag == 'features':
            vals.features = [SamuraiTitleFeature._parse(feature) for feature in child.feature]
        elif tag == 'play_styles':
            xmlutils.validate_schema(child, {'play_style': {
                'controllers': {'controller': {'id': None, 'name': None, 'icons': {'icon': None}}},
                'features': {'feature': SamuraiTitleFeature._get_schema()[0]}}
            }, True)
            vals.play_styles = []
            for play_style in child.play_style:
                if hasattr(play_style, 'controllers'):
                    controllers = [
                        SamuraiTitleController(
                            utils.misc.get_bool(controller.get('required')),
                            int(controller.get('type')),
                            int(controller.id.text),
                            controller.name.text,
                            [common.SamuraiIcon._parse(icon) for icon in controller.icons.icon] if hasattr(controller, 'icons') else None
                        )
                        for controller in play_style.controllers.controller
                    ]
                else:
                    controllers = []
                if hasattr(play_style, 'features'):
                    features = [SamuraiTitleFeature._parse(feature) for feature in play_style.features.feature]
                else:
                    features = []
                vals.play_styles.append(SamuraiTitlePlayStyle(play_style.get('type'), controllers, features))
        elif tag == 'languages':
            vals.languages = []
            for language in child.language:
                xmlutils.validate_schema(language, {'iso_code': None, 'name': None}, False)
                vals.languages.append(SamuraiTitleLanguage(language.iso_code.text, language.name.text))
        elif tag == 'number_of_players':
            # sometimes this field contains additional text in a second line, discard it for now and use the first non-empty line
            cleaned_text = next(line for line in text.replace('<br>', '\n').split('\n') if line)
            matches = re.search(r'(\d+)(?:\s*-\s*(\d+))?', cleaned_text)
            if matches:
                vals.num_players = (int(matches[1]), int(matches[2] or matches[1]))
            elif cleaned_text.startswith('*'):  # disclaimer instead of specific player numbers (example: 50010000037675)
                vals.num_players = None
            elif re.search(r'[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff66-\uff9f]', cleaned_text):  # ignore errors if text contains japanese/chinese/korean characters
                vals.num_players = None
            else:
                raise RuntimeError(f'Could not parse player details: {text}')
            vals.num_players_raw = text
        elif tag == 'disclaimer':
            vals.disclaimer = text
        elif tag == 'copyright':
            xmlutils.validate_schema(child, {'text': None, 'image_url': None}, True)
            vals.copyright = SamuraiTitleCopyright(child.find('text').text, xmlutils.get_text(child, 'image_url'))
        elif tag == 'screenshots':
            vals.screenshots = [SamuraiTitleScreenshot._parse(screenshot) for screenshot in child.screenshot]
        elif tag == 'main_images':
            vals.main_images = [SamuraiTitleScreenshot._parse(image) for image in child.image]
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
                xmlutils.validate_schema(website, {'name': None, 'url': None, 'official': None}, False)
                vals.websites.append(SamuraiTitleWebsite(
                    website.name.text,
                    website.url.text,
                    utils.misc.get_bool(website.official.text)
                ))
        elif tag == 'movies':
            vals.movies = [movie_list.SamuraiListMovie._parse(m) for m in child.movie]
        elif tag == 'demo_titles':
            vals.demos = [
                SamuraiTitleLinkedDemo(
                    ids.ContentID(demo.get('id')),
                    demo.name.text,
                    xmlutils.get_text(demo, 'icon_url')
                )
                for demo in child.demo_title
            ]
        elif tag == 'peripheral_description':
            vals.peripheral_description = text
        elif tag == 'network_feature_description':
            vals.network_feature_description = text
        elif tag == 'spec_description':
            vals.spec_description = text
        elif tag == 'data_size':
            vals.size = int(text)
        elif tag == 'save_data_count':
            vals.save_data_count = text
        elif tag == 'save_data_volume':
            vals.save_data_volume = text
        elif tag == 'catch_copy':
            vals.catch_copy = text
        elif tag == 'shared_movies':
            vals.shared_movies = [SamuraiSharedMovie._parse(movie) for movie in child.shared_movie]
        elif tag == 'title_notices':
            xmlutils.validate_schema(child, {'title_notice': {'url': None, 'display_name': None, 'description': None}}, False)
            vals.title_notices = [
                SamuraiTitleNotice(
                    notice.get('type'),
                    notice.url.text,
                    notice.display_name.text,
                    notice.description.text
                )
                for notice in child.title_notice
            ]
        elif tag == 'title_metas':
            xmlutils.validate_schema(child, {'title_meta': {'value': None}}, False)
            vals.title_metas = [(m.get('type'), m.value.text) for m in child.title_meta]
        elif tag == 'digital_manuals':
            xmlutils.validate_schema(child, {'digital_manual': {'name': None, 'url': None}}, False)
            vals.digital_manuals = [SamuraiDigitalManual(manual.name.text, manual.url.text) for manual in child.digital_manual]
        elif tag == 'aoc_infos':
            vals.aoc_infos = text
        else:
            return super()._try_parse_value(vals, child, tag, text, custom_types)
        return True


# TODO: DRY (title.py, movie.py)
@dataclass(frozen=True)
class SamuraiTitleElement(_SamuraiTitleOptionalMixin, _SamuraiTitleBaseMixin):
    @classmethod
    def _parse(cls, xml: lxml.objectify.ObjectifiedElement) -> 'SamuraiTitleElement':
        vals = utils.misc.dotdict()

        for child, tag, text in xmlutils.iter_children(xml):
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
        title_xml = xmlutils.load_root(reader, 'title')
        self.title = SamuraiTitleElement._parse(title_xml)
