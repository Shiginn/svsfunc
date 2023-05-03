from __future__ import annotations

import os
import re
from functools import partial
from pathlib import Path
from typing import Any, Callable, NoReturn, TypeVar, TYPE_CHECKING

from vstools import (
    ChromaLocation, ColorRange, FrameRangeN, FrameRangesN, Matrix, Primaries, Transfer, VSMapValue, core, get_prop,
    normalize_ranges, to_arr, vs, DataType
)

from .custom_types import FramePropKey

if TYPE_CHECKING:
    from .indexer import Indexer

__all__ = [
    "trim", "write_props",
    "get_lsmas_cachefile",
    "normalize_list"
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
    :param alignment:   Where to write props on the clip (see .text.Text), defaults to 7
    :param scale:       Scale of the text (see .text.Text), defaults to 1

    :raises KeyError:   If requested prop is not supported

    :return:            Clip with frame props
    """
    prop_map: dict[FramePropKey, tuple[str, type[VSMapValue], Callable[[Any], str]]] = {
        "_PictType": ("Picture Type", bytes, lambda x: x.decode()),  # type: ignore
        "_ChromaLocation": ("Chroma Location", int, lambda x: ChromaLocation(x).pretty_string),
        "_Primaries": ("Primaries", int, lambda x: Primaries(x).pretty_string),
        "_Transfer": ("Transfer", int, lambda x: Transfer(x).pretty_string),
        "_Matrix": ("Matrix", int, lambda x: Matrix(x).pretty_string),
        "_ColorRange": ("Color Range", int, lambda x: ColorRange(x).pretty_string)
    }

    def _get_props(n: int, f: vs.VideoFrame, clip: vs.VideoNode, props: list[FramePropKey]) -> vs.VideoNode:
        txt = f"{'Frame Info' if clip_name is None else clip_name}\nFrame Number: {n}"

        for prop in props:
            if prop not in prop_map:
                raise KeyError(f"write_props: unable to find prop \"{prop}\"")

            prop_name, prop_type, convert_func = prop_map[prop]
            prop_value = get_prop(f, prop, prop_type)

            txt += f"\n{prop_name}: {convert_func(prop_value)}"

        return clip.text.Text(txt, alignment=alignment, scale=scale)

    f = partial(_get_props, clip=clip, props=to_arr(props))
    return clip.std.FrameEval(f, prop_src=clip)


def get_lsmas_cachefile(source: str | Path, indexer: Indexer[vs.VideoNode] | None = None) -> Path:
    """
    Guess lsmas cache file path based on input path, indexer settings and lsmas build options.

    :param source:          Input file path
    :param indexer:         Indexer used (must be keyword arguments), defaults to None

    :raises ValueError:     If cache directory cannot be guessed or is invalid

    :return:                lsmas cache file path
    """
    source = Path(source) if isinstance(source, str) else source
    source_lwi = str(
        source.resolve().with_suffix(source.suffix + ".lwi")
    ).replace(":", "_").replace("/", "_").replace("\\", "_")

    cachedir: DataType | None = indexer.kwargs.get("cachedir", None) if indexer is not None else None
    cachedir = str(cachedir, "utf8") if cachedir is not None else cachedir  # type: ignore

    if cachedir is None:
        config: bytes = core.lazy.lsmas.Version()["config"]  # type: ignore
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
