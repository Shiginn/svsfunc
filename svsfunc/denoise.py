__all__ = ["BM3DMode", "BM3D"]

from enum import IntEnum
from typing import Any, Callable, Sequence

import vapoursynth as vs
from vskernels import Catrom, Kernel
from vstools import Matrix, depth, get_depth

core = vs.core


class BM3DMode(IntEnum):
    CPU = 0
    CUDA = 1
    CUDA_RTC = 2

    @property
    def funcs(self) -> list[Callable[..., vs.VideoNode]]:
        return [
            core.bm3dcpu.BM3D,
            core.bm3dcuda.BM3D,
            core.bm3dcuda_rtc.BM3D
        ]


def yuv_to_opp(clip: vs.VideoNode, matrix: int, resizer: Kernel) -> vs.VideoNode:
    return core.bm3d.RGB2OPP(resizer.resample(clip, format=vs.RGBS, matrix_in=matrix), 1)


def opp_to_yuv(clip: vs.VideoNode, matrix: int, src_format: vs.VideoFormat, resizer: Kernel) -> vs.VideoNode:
    sample = (src_format.bits_per_sample == 32)
    return resizer.resample(core.bm3d.OPP2RGB(clip, sample), format=src_format, matrix=matrix)


def BM3D(
    clip: vs.VideoNode, sigma: float | Sequence[float], ref: vs.VideoNode | None = None,
    matrix: Matrix | int | None = None, mode: BM3DMode = BM3DMode.CPU, resizer: Kernel = Catrom(),
    **bm3d_args: Any
) -> vs.VideoNode:
    """
    Small BM3D wrapper while waiting for vs-denoise

    :param clip:        VideoNode to denoise.
    :param sigma:       Denoise strength, can be specified for each plane.
    :param ref:         Reference clip to used in BM3D. Must have the same format as `clip`.
    :param matrix:      Input clip matrix. If None, will try to extract from frame props.
                        If prop is not set, you must specify the matrix.
    :param mode:        BM3D mode to use. CUDA is faster but requires Nvidia GPU.
    :param bm3d_args:   Additional parameters to pass to BM3D.

    :return:            Denoised clip.
    """
    assert clip.format

    is_gray = (clip.format.color_family == vs.GRAY)
    matrix = matrix or Matrix.from_video(clip, strict=True)

    if ref is not None:
        assert ref.format
        if ref.format != clip.format:
            raise ValueError("BM3D: clip and ref must have the same format")
        ref = yuv_to_opp(clip, matrix, resizer) if not is_gray else resizer.resample(clip, format=vs.GRAYS)

    clip_opp = yuv_to_opp(clip, matrix, resizer) if not is_gray else resizer.resample(clip, format=vs.GRAYS)

    rad: int = bm3d_args.pop("radius", 2)
    func = mode.funcs[mode.value]
    bm3d = func(clip_opp, sigma=sigma, ref=ref, radius=rad, **bm3d_args).bm3d.VAggregate(rad, 1)
    bm3d = func(clip_opp, sigma=sigma, ref=bm3d, radius=rad, **bm3d_args).bm3d.VAggregate(rad, 1)

    if not is_gray:
        bm3d = opp_to_yuv(bm3d, matrix, clip.format, resizer)

    return depth(bm3d, get_depth(clip))
