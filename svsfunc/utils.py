from vstools import FrameRangeN, FrameRangesN, normalize_ranges, vs

__all__ = ["trim"]


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
