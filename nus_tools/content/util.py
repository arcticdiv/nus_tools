import contextlib
from abc import abstractmethod
from pathlib import Path
from typing import Any, BinaryIO, ContextManager, Iterator, List, Optional, Tuple, cast

from reqcli.source import UnloadableType
from reqcli.type import TypeLoadConfig

from .app import AppDataReader, AppDecryptor, AppBlockReader, FSTProcessor
from .. import ids
from ..sources.contentcdn import _ContentServerBase
from ..types.contentcdn import TMD
from ..utils import misc as misc_utils


class BaseContentUtil:
    def __init__(
        self,
        title_id: ids.TTitleIDInput,
        decrypted_titlekey: Optional[bytes],
        *,
        verify: bool,
        config: Optional[TypeLoadConfig],
    ):
        self._title_id = ids.TitleID.get_inst(title_id)
        self._decrypted_titlekey = decrypted_titlekey
        self._verify = verify
        self._config = config

    @abstractmethod
    def get_h3(self, entry_id: int) -> ContextManager[BinaryIO]:
        pass

    @abstractmethod
    def get_app(self, entry_id: int) -> ContextManager[Tuple[BinaryIO, int]]:
        pass

    @abstractmethod
    def _get_tmd_raw(self) -> bytes:
        pass

    @contextlib.contextmanager
    def get_reader(self, tmd_entry: Any) -> Iterator[AppDataReader]:
        h3: Optional[bytes]
        if tmd_entry.type.hashed:
            with self.get_h3(tmd_entry.id) as reader:
                h3 = reader.read()
        else:
            h3 = None

        with self.get_app(tmd_entry.id) as (app, app_size):
            assert app_size is not None, 'app stream must have a size'
            block_reader: AppBlockReader

            if tmd_entry.type.encrypted:
                assert self._decrypted_titlekey
                block_reader = AppDecryptor(
                    self._decrypted_titlekey,
                    tmd_entry.index,
                    h3,
                    app,
                    tmd_entry.sha1,
                    app_size,
                    tmd_entry.size,
                    verify=self._verify,
                )
            else:
                block_reader = AppBlockReader(
                    h3,
                    app,
                    tmd_entry.sha1,
                    app_size,
                    tmd_entry.size,
                    verify=self._verify,
                )

            yield AppDataReader(block_reader)

    def get_fst(self) -> FSTProcessor:
        with self.get_reader(self.tmd.data.contents[0]) as reader:
            return FSTProcessor.try_load(reader.block_reader)

    @misc_utils.cachedproperty
    def tmd(self) -> TMD:
        return TMD(self._title_id).load_bytes(self.tmd_raw, self._config)

    @misc_utils.cachedproperty
    def tmd_raw(self) -> bytes:
        return self._get_tmd_raw()


class DownloadContentUtil(BaseContentUtil):
    def __init__(
        self,
        ccs: _ContentServerBase,
        title_id: ids.TTitleIDInput,
        decrypted_titlekey: Optional[bytes],
        *,
        verify: bool = True,
    ):
        super().__init__(
            title_id,
            decrypted_titlekey,
            verify=verify,
            config=ccs._config.type_load_config,
        )
        self._ccs = ccs

    @contextlib.contextmanager
    def get_h3(self, entry_id: int) -> Iterator[BinaryIO]:
        with self._ccs.get_h3(self._title_id, entry_id).get_reader() as reader:
            yield reader

    @contextlib.contextmanager
    def get_app(self, entry_id: int) -> Iterator[Tuple[BinaryIO, int]]:
        with self._ccs.get_app(self._title_id, entry_id).get_reader() as reader:
            assert reader.size is not None, 'app stream does not have a size'
            yield reader, reader.size

    def _get_tmd_raw(self) -> bytes:
        with cast(UnloadableType, self._ccs.get_tmd(self._title_id, force_unloadable=True)).get_reader() as tmd_reader:
            return tmd_reader.read()


class LocalDirectoryContentUtil(BaseContentUtil):
    def __init__(
        self,
        directory: str,
        title_id: ids.TTitleIDInput,
        decrypted_titlekey: Optional[bytes],
        *,
        verify: bool = True,
        config: Optional[TypeLoadConfig] = None,
    ):
        super().__init__(title_id, decrypted_titlekey, verify=verify, config=config)
        self._directory = Path(directory)

    def get_h3(self, entry_id: int) -> ContextManager[BinaryIO]:
        file_path = self.__find_case_insensitive([f'{entry_id:08x}.h3'])
        return file_path.open('rb')

    @contextlib.contextmanager
    def get_app(self, entry_id: int) -> Iterator[Tuple[BinaryIO, int]]:
        targets = [f'{entry_id:08x}', f'{entry_id:08x}.app']
        file_path = self.__find_case_insensitive(targets)

        with file_path.open('rb') as f:
            yield f, file_path.stat().st_size

    def _get_tmd_raw(self) -> bytes:
        file_path = self.__find_case_insensitive(['title.tmd', 'tmd'])
        return file_path.read_bytes()

    def __find_case_insensitive(self, targets: List[str]) -> Path:
        for target in targets:
            target = target.lower()
            found = next((p for p in self._directory.glob('*') if p.name.lower() == target), None)
            if found:
                return found
        # not found
        s = ' or '.join(f'\'{t}\'' for t in targets)
        raise RuntimeError(f'Unable to find {s} in \'{self._directory}\'')
