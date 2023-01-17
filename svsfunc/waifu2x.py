__all__ = ["Waifu2x", "Waifu2xBackend"]

import warnings
from enum import IntEnum
from typing import Any, Literal

from vskernels import Catrom
from vstools import Matrix, core, depth, get_depth, get_plane_sizes, get_y, vs


class Waifu2xBackend(IntEnum):
    OV_CPU = 0
    ORT_CPU = 1
    ORT_CUDA = 2
    TRT = 2


class Waifu2x:
    """Waifu2x wrapper using CUNet model"""
    waifu2x_args: dict[str, Any]

    def __init__(
        self, noise: Literal[-1, 0, 1, 2, 3], backend: Waifu2xBackend = Waifu2xBackend.TRT,
        backend_args: dict[str, Any] | None = None, **kwargs: Any
    ) -> None:
        """
        Waifu2x wrapper using CUNet model

        :param noise:   Waifu2x denoise level (-1 = None, 0-3 to adjust denoise strength)
        :param backend: vs-mlrt backend
        """
        from vsmlrt import Backend, Waifu2xModel, backendT

        if "model" in kwargs:
            raise ValueError("Waifu2x: Cannot override model.")

        backends: list[backendT] = [Backend.OV_CPU, Backend.ORT_CPU, Backend.ORT_CUDA, Backend.TRT]
        mlrt_backend = backends[backend.value]
        if backend_args is not None:
            mlrt_backend = mlrt_backend(**backend_args)

        self.waifu2x_args = dict(noise=noise, backend=mlrt_backend, model=Waifu2xModel.cunet, **kwargs)


    def chroma_recon(
        self, clip: vs.VideoNode, matrix: int | None = None, fast: bool = True, **w2x_overrides: Any
    ) -> vs.VideoNode:
        """
        Reconstruct chroma planes of a clip using Waifu2x. Using `fast=True` will downscale luma to chroma size and
        then perform chroma reconstruction. Performance is better but quality is worse. Using `fast=True` on YUV444
        clip is useless. `fast=False` upscale chroma to luma size using Catrom and then perform chroma reconstruction.

        :param clip:            Clip to reconstruct
        :param matrix:          Clip matrix
        :param fast:            Wether or not to use fast mode
        :param w2x_overrides:   Override Waifu2x settings. `scale` cannot be changed.
        """
        from vsmlrt import Waifu2x
        assert clip.format

        matrix = matrix or Matrix.from_video(clip, strict=True)

        if fast:
            chroma_w, chroma_h = get_plane_sizes(clip, 1)
            if (chroma_w, chroma_h) == (clip.width, clip.height):
                warnings.warn("Waifu2x.chroma_recon: using fast mode on YUV444 is useless.")

            luma_down = Catrom.scale(get_y(clip), chroma_w, chroma_h)
            clip_down = core.std.ShufflePlanes([luma_down, clip], [0, 1, 2], vs.YUV)
        else:
            clip_down = clip

        clip_rgb = Catrom.resample(clip_down, vs.RGBS, matrix_in=matrix)
        w2x = Waifu2x(clip_rgb, **(self.waifu2x_args | w2x_overrides | dict(scale=1)))

        yuv_format = clip.format.replace(subsampling_h=0, subsampling_w=0) if fast else clip.format
        w2x_yuv = Catrom.resample(w2x, yuv_format, matrix=matrix)

        return core.std.ShufflePlanes([clip, w2x_yuv], [0, 1, 2], vs.YUV)


    def double(self, clip: vs.VideoNode, **w2x_overrides: Any) -> vs.VideoNode:
        """
        Upscale a clip 2x using Waifu2x. Only process luma, chroma should be handled separately.

        :param clip:            Clip to upscale.
        :param w2x_overrides:   Override Waifu2x settings. `scale` cannot be changed.
        """
        from vsmlrt import Waifu2x
        clip_rgb = get_y(clip).std.ShufflePlanes(0, vs.RGB)

        up = Waifu2x(clip_rgb, **(self.waifu2x_args | w2x_overrides | dict(scale=2)))
        up = up.std.ShufflePlanes(0, vs.GRAY)
        up = up.akarin.Expr("x 0.5 255 / +")

        return depth(up, get_depth(clip))
