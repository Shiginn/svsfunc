from __future__ import annotations

import os
import re
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, NoReturn, TypeVar
from vardautomation import FileInfo

from vstools import (
    ChromaLocation, ColorRange, FrameRangeN, FrameRangesN, Matrix, Primaries, Transfer, core, get_prop,
    normalize_ranges, to_arr, vs
)

from .custom_types import FramePropKey, PathLike

if TYPE_CHECKING:
    from .indexer import Indexer, FileInfoIndexer

__all__ = [
    "trim", "write_props", "clip_from_indexer",
    "get_lsmas_cachefile",
    "ensure_path", "normalize_list"
]

T = TypeVar("T")


def trim(clip: vs.VideoNode, frame_range: FrameRangeN | FrameRangesN) -> vs.VideoNode:
    """
    Trim clip to keep only selected frames. Ranges are inclusives.

    :param clip:            Clip to trim
    :param frame_range:     Frames to keep

    :raises ValueError:     If no ranges are given

    :return:                Trimmed clip
    """
    ranges = normalize_ranges(clip, frame_range)
    if not ranges:
        raise ValueError("trim: Cannot trim clip with empty range")

    s, e = ranges.pop(0)
    trim_clip = clip[s:e + 1]

    for (s, e) in ranges:
        trim_clip += clip[s:e + 1]

    return trim_clip


def write_props(
    clip: vs.VideoNode, props: FramePropKey | list[FramePropKey] = "_PictType", clip_name: str | None = None,
    alignment: int = 7, scale: int = 1
) -> vs.VideoNode:
    """
    Write frame props on a clip

    :param clip:        Clip to get frame props from
    :param props:       Frame props to write, defaults to "_PictType"
    :param clip_name:   Name of the clip, defaults to None
    :param alignment:   Where to write props on the clip (see text plugin), defaults to 7
    :param scale:       Scale of the text (see text plugin), defaults to 1

    :raises KeyError:   If requested prop is not supported or not found.

    :return:            Clip with frame props
    """
    prop_map: dict[FramePropKey, tuple[str, Callable[[Any], str]]] = {
        "_PictType": ("Picture Type", lambda x: x.decode()),  # type: ignore
        "_ChromaLocation": ("Chroma Location", lambda x: ChromaLocation(x).pretty_string),
        "_Primaries": ("Primaries", lambda x: Primaries(x).pretty_string),
        "_Transfer": ("Transfer", lambda x: Transfer(x).pretty_string),
        "_Matrix": ("Matrix", lambda x: Matrix(x).pretty_string),
        "_ColorRange": ("Color Range", lambda x: ColorRange(x).pretty_string)
    }

    def _get_props(n: int, f: vs.VideoFrame, clip: vs.VideoNode, props: list[FramePropKey]) -> vs.VideoNode:
        txt = f"{'Frame Info' if clip_name is None else clip_name}\nFrame Number: {n}"

        for prop in props:
            if prop not in prop_map:
                raise KeyError(f"write_props: unsupported prop \"{prop}\".")
            if prop not in f.props:
                raise KeyError(f"write_props: prop \"{prop}\" not found in frame {n}.")

            prop_name, convert_func = prop_map[prop]
            prop_value: bytes | int = get_prop(f, prop, bytes if prop == "_PictType" else int)

            txt += f"\n{prop_name}: {convert_func(prop_value)}"

        return clip.text.Text(txt, alignment=alignment, scale=scale)

    f = partial(_get_props, clip=clip, props=to_arr(props))
    out = clip.std.FrameEval(f, prop_src=clip)

    return out.std.SetFrameProp("Name", data=clip_name) if clip_name else out



def clip_from_indexer(
    source: PathLike, indexer: Indexer[vs.VideoNode] | FileInfoIndexer, ignore_trims: bool
) -> vs.VideoNode:
    """
    Get the indexed clip from any indexer

    :param source:          Source file path
    :param indexer:         Indexer to use
    :param ignore_trims:    Get untrimmed clip even if the indexer has trims

    :return: Indexed clip
    """
    clip = indexer(source)
    if isinstance(clip, FileInfo):
        clip = clip.clip if ignore_trims else clip.clip_cut

    return clip


def get_lsmas_cachefile(source: PathLike) -> Path:
    """
    Guess lsmas cache file path based on input path and lsmas build options.

    :param source:          Input file path
    :param indexer:         Indexer used, defaults to None

    :raises ValueError:     If cache directory cannot be guessed or is invalid

    :return:                lsmas cache file path
    """
    source = ensure_path(source, "get_lsmas_cachefile")

    source_lwi = str(
        source.resolve().with_suffix(source.suffix + ".lwi")
    ).replace(":", "_").replace("/", "_").replace("\\", "_")

    config: bytes = core.lsmas.Version()["config"]  # type: ignore
    regex = re.match("-Dcachedir=\"(.*)\"", config.decode())
    if regex is None:
        raise ValueError("get_lsmas_cache: Could not find cache directory")

    cachedir = regex.group(1)

    def _from_getenv(env: str) -> Path | NoReturn:
        env_dir = os.getenv(env)
        if env_dir is None:
            raise ValueError(f"get_lsmas_cache: Environment variable \"{env}\" is missing")
        return Path(env_dir) / source_lwi

    match cachedir:
        case '""' | "": return source.with_suffix(source.suffix + ".lwi")
        case ".": return Path.cwd() / source_lwi
        case "/tmp": return Path("/tmp") / source_lwi
        case "getenv(\"TMPDIR\")": return _from_getenv("TMPDIR")
        case "getenv(\"TEMP\")": return _from_getenv("TEMP")
        case _: raise ValueError("get_lsmas_cache: Invalid cache directory found")


def ensure_path(path: str | Path, source: str = "ensure_path") -> Path:
    if isinstance(path, str):
        path = Path(path)

    if not path.exists():
        raise ValueError(f"{source}: path \"{path}\" does not exist.")

    return path.resolve()


def normalize_list(val: list[T] | T, max_size: int, padding: T, source: str) -> NoReturn | list[T]:
    """
    Normalize a list to match the given length

    :param val:         List to normalize. If not a list, will be converted to a list of max_size elements.
    :param max_size:    Maximum number of element in the list.
    :param padding:     Object to use to pad the list if its length is lesser than max_size
    :param source:      Caller function name

    :raises ValueError: If the input list's length is greater than max_size

    :return:            Padded list
    """
    if not isinstance(val, list):
        return [val] * max_size

    input_size = len(val)

    if input_size > max_size:
        raise ValueError(f"{source}: Too many elements given, expected 0-{max_size}, got {input_size}.")
    elif input_size < max_size:
        return val + [padding] * (max_size - input_size)
    else:
        return val
