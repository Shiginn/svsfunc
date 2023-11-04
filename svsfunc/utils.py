from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Any, Callable, NoReturn, TypeVar

from vstools import (
    ChromaLocation, ColorRange, FrameRangeN, FrameRangesN, Matrix, Primaries, Transfer, get_prop, normalize_ranges,
    to_arr, vs
)

from .custom_types import FramePropKey

__all__ = [
    "trim", "write_props",
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
