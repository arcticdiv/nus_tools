from construct import Container
from typing import Optional, Union, overload
from reqcli.type import BaseTypeLoadableConstruct

from .. import common
from ... import structs, ids


class Ticket(BaseTypeLoadableConstruct):
    data: Container

    def __init__(self, title_id: Optional[ids.TTitleIDInput] = None):
        self.__title_id = ids.TitleID.get_inst(title_id) if title_id else None
        super().__init__(structs.ticket)

    def _read(self, reader, config):
        raw_data = reader.read()
        self.data = self._parse_construct(raw_data, config)

        if self.__title_id:
            # sanity check
            assert self.data.title_id == self.__title_id

        common.SignatureHandler.maybe_verify(
            config,
            self.data.__raw_signed__,
            self.data.issuer,
            self.data.signature,
            self.data.certificates
        )


class TMD(BaseTypeLoadableConstruct):
    data: Container

    @overload
    def __init__(self, title_id: ids.TTitleIDInput):
        ...

    @overload
    def __init__(self, platform: ids.AnyPlatform):
        ...

    def __init__(self, title_id: Optional[Union[ids.TTitleIDInput, ids.AnyPlatform]] = None, platform: Optional[ids.AnyPlatform] = None):  # type: ignore
        if title_id is None:
            # kwarg platform
            self.__title_id = None
            assert platform is not None
        elif isinstance(title_id, (ids.TitlePlatform, ids.ContentPlatform)):
            # arg platform
            self.__title_id = None
            platform = title_id
        else:
            # arg/kwarg title_id
            self.__title_id = ids.TitleID.get_inst(title_id)
            platform = self.__title_id.type.platform
        super().__init__(structs.tmd.get(platform))

    def _read(self, reader, config):
        raw_data = reader.read()
        self.data = self._parse_construct(raw_data, config)

        if self.__title_id:
            # sanity check
            assert self.data.title_id == self.__title_id

        common.SignatureHandler.maybe_verify(
            config,
            self.data.__raw_header_signed__,
            self.data.issuer,
            self.data.signature,
            self.data.certificates
        )
