from __future__ import annotations

from pathlib import Path
from typing import Literal, TypeAlias, TypeVar, Union

from vsmuxtools import src_file
from vstools import vs, vs_object

__all__ = [
    "BaseVsObject",
    "HoldsVideoNodeT", "IndexedT",
    "PathLike", "FramePropKey"
]


# for some reasons, docs build fails when inheriting from vs_object directly but not when inherinting from this
class BaseVsObject(vs_object):
    ...

IndexedT = TypeVar("IndexedT", vs.VideoNode, vs.AudioNode, src_file)
HoldsVideoNodeT = TypeVar("HoldsVideoNodeT", vs.VideoNode, src_file)

PathLike: TypeAlias = Union[str, Path]

FramePropKey: TypeAlias = Literal["_PictType", "_ChromaLocation", "_Primaries", "_Transfer", "_Matrix", "_ColorRange"]
