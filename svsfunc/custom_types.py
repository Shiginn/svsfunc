from __future__ import annotations

from pathlib import Path
from typing import Literal, TypeAlias, TypeVar, Union

from vsmuxtools import src_file
from vstools import vs

__all__ = ["HoldsVideoNodeT", "PathLike", "FramePropKey"]

HoldsVideoNodeT = TypeVar("HoldsVideoNodeT", vs.VideoNode, src_file)

PathLike: TypeAlias = Union[str, Path]

FramePropKey: TypeAlias = Literal["_PictType", "_ChromaLocation", "_Primaries", "_Transfer", "_Matrix", "_ColorRange"]
