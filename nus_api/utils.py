import io
import os
import lxml.objectify
from xml.etree import ElementTree as ET
from typing import Callable, Iterator, Optional, Tuple, Dict, Set


class BytesIterator(Iterator[bytes]):
    def __init__(self, read_func: Callable[[], bytes]):
        self.__read_func = read_func

    def __next__(self):
        data = self.__read_func()
        if data == b'':
            raise StopIteration
        return data

    def read_all(self):
        return b''.join(self)


class CachingIterator(BytesIterator):
    def __init__(self, filename: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filename = filename
        self.tmp_filename = f'{filename}.tmp'
        self.__file = None

    def __next__(self):
        data = super().__next__()
        self.__file.write(data)
        return data

    def __enter__(self):
        os.makedirs(os.path.dirname(self.tmp_filename), exist_ok=True)
        self.__file = open(self.tmp_filename, 'wb')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # finish writing in case not everything was read
        for data in self:
            self.__file.write(data)
        self.__file.close()
        self.__file = None

        # move tmp file if successful
        if exc_type is None:
            os.rename(self.tmp_filename, self.filename)


def get_bool(text: str) -> bool:
    text = text.lower()
    if text in ['true', 'yes', 'y', '1']:
        return True
    elif text in ['false', 'no', 'n', '0']:
        return False
    raise ValueError(text)


def is_dict_subset_deep(a: Optional[Dict], b: Optional[Dict]) -> bool:
    if a is None:
        return True
    elif b is None:
        return False

    try:
        for k, v in a.items():
            other_v = b[k]
            if type(v) == dict:
                if not other_v or type(other_v) != dict:
                    return False
                if not is_dict_subset_deep(v, other_v):
                    return False
            else:
                if v is not None and v != other_v:
                    return False
    except KeyError:
        return False
    return True


class dotdict(dict):
    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, attr, value):
        self.__setitem__(attr, value)

    def __delattr__(self, attr):
        self.__delitem__(attr)


class xml:
    @staticmethod
    def read(data: bytes) -> ET.ElementTree:
        return ET.parse(io.BytesIO(data))

    @staticmethod
    def read_object(data: bytes) -> lxml.objectify.ObjectifiedElement:
        return lxml.objectify.parse(io.BytesIO(data)).getroot()

    @staticmethod
    def read_iterator_object(it: BytesIterator, root_tag: Optional[str] = None) -> lxml.objectify.ObjectifiedElement:
        data = it.read_all()
        tree = xml.read_object(data)
        children = tree.getchildren()
        assert len(children) == 1
        if root_tag:
            assert children[0].tag == root_tag
        return children[0]

    @staticmethod
    def get_text(xml, attr: str) -> Optional[str]:
        val = getattr(xml, attr, None)
        return val.text if val is not None else None

    @staticmethod
    def iter_children(xml) -> Iterator[Tuple[lxml.objectify.ObjectifiedElement, str, str]]:
        for child in xml.getchildren():
            yield (child, child.tag, child.text)

    @classmethod
    def get_tag_schema(cls, xml) -> Optional[Dict]:
        children = xml.getchildren()
        if not children:
            return None

        d = {}
        for c in children:
            d[c.tag] = cls.get_tag_schema(c)
        return d

    @classmethod
    def validate_schema(cls, xml, target_hierarchy: Optional[Dict], superset: bool):
        h = cls.get_tag_schema(xml)
        if (not superset and target_hierarchy != h) or (superset and not is_dict_subset_deep(h, target_hierarchy)):
            raise RuntimeError(f'unexpected XML structure\nexpected{" subset of" if superset else ""}:\n\t{target_hierarchy}\ngot:\n\t{h}')

    @classmethod
    def get_child_tags(cls, xml) -> Set[str]:
        return {el.tag for el in xml.getchildren()}
