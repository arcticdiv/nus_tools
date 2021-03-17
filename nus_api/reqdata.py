import urllib.parse
from dataclasses import dataclass, field
from typing import Optional, Union, Tuple


# ref: cert parameter for https://requests.readthedocs.io/en/master/api/#requests.request
CertType = Union[str, Tuple[str, str]]


@dataclass(frozen=True)
class ReqData:
    path: str
    params: dict = field(default_factory=lambda: {})
    headers: dict = field(default_factory=lambda: {})
    cert: Optional[CertType] = None

    def __add__(self, other: 'ReqData') -> 'ReqData':
        return ReqData(
            urllib.parse.urljoin(self.path, other.path),
            {**self.params, **other.params},
            {**self.headers, **other.headers},
            self.cert or other.cert
        )
