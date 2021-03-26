from typing import Dict, Optional


class dotdict(dict):
    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, attr, value):
        self.__setitem__(attr, value)

    def __delattr__(self, attr):
        self.__delitem__(attr)


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
