from abc import abstractmethod
from pathlib import Path
from typing import Callable, Protocol, TypeAlias, TypeVar, runtime_checkable

from vardautomation import FileInfo, FileInfo2
from vstools import vs

FileInfoT = TypeVar("FileInfoT", FileInfo, FileInfo2)
IndexedT = TypeVar("IndexedT", vs.VideoNode, FileInfo, FileInfo2)
VSIdxFunc: TypeAlias = Callable[[str | Path], vs.VideoNode]


# Extracted from VS stubs
@runtime_checkable
class SupportsString(Protocol):
    @abstractmethod
    def __str__(self) -> str:
        ...


VSDataType: TypeAlias = str | bytes | bytearray | SupportsString
