import abc
import requests
from typing import Union

from ..config import Configuration
from ..reqdata import ReqData
from ..types._base import BaseType


class BaseSource(abc.ABC):
    def __init__(self, base_reqdata: ReqData, *, verify_tls: bool = True):
        self._verify_tls = verify_tls
        self._base_reqdata = ReqData(
            path='',
            headers={'User-Agent': Configuration.default_user_agent}
        )
        self._base_reqdata += base_reqdata

    # TODO: ratelimit by hostname
    def _get(self, data: Union[ReqData, BaseType], **kwargs) -> requests.Response:
        if isinstance(data, BaseType):
            reqdata = data._merged_reqdata
        else:
            reqdata = self._base_reqdata + data
        return requests.get(
            url=reqdata.path,
            headers=reqdata.headers,
            params=reqdata.params,
            cert=reqdata.cert,
            verify=self._verify_tls,
            **kwargs
        )
