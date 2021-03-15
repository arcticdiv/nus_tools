import urllib.parse
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReqData:
    path: str
    params: dict = field(default_factory=lambda: {})
    headers: dict = field(default_factory=lambda: {})

    def __add__(self, other: 'ReqData') -> 'ReqData':
        return ReqData(
            urllib.parse.urljoin(self.path, other.path),
            {**self.params, **other.params},
            {**self.headers, **other.headers}
        )
