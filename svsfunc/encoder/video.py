__all__ = ["VideoTooling"]

from typing import Any, Callable, Dict, List, Tuple, Type, Union

import vapoursynth as vs
from vardautomation import FFV1, X264, X265, NVEncCLossless, VPath, logger

from .base import BaseEncoder

VideoEncoders = Union[X264, X265]
VideoLosslessEncoders = Union[FFV1, NVEncCLossless]


class VideoTooling(BaseEncoder):
    v_encoder: VideoEncoders | None = None
    v_lossless_encoder: VideoLosslessEncoders | None = None

    qp_file: vs.VideoNode | None = None
    post_filterchain_func: Callable[[VPath], vs.VideoNode] | None = None

    def video_encoder(
        self, encoder: Type[VideoEncoders],
        settings: str | List[str] | Dict[str, Any],
        zones: Dict[Tuple[int, int], Dict[str, Any]] | None = None,
        resumable: bool = False, prefetch: int = 0,
        qp_file: bool | vs.VideoNode | None = None,
        **overrides: Any
    ) -> None:
        self.v_encoder = encoder(settings, zones, **overrides)
        self.v_encoder.resumable = resumable
        self.v_encoder.prefetch = prefetch

        logger.info(f"Video Encoder: {encoder.__name__}")
        logger.info(f"Zones: {zones}")

        if isinstance(qp_file, vs.VideoNode):
            self.qp_file = qp_file
            logger.info("Using custom VideoNode for qp_file")
        elif qp_file:
            self.qp_file = self.file.clip_cut
            logger.info("Using file.clip_cut for qp_file")


    def video_lossless_encoder(
        self, lossless_encoder: Type[VideoLosslessEncoders],
        post_filterchain_func: Callable[[VPath], vs.VideoNode] | None = None,
        **overrides: Any
    ) -> None:

        self.v_lossless_encoder = lossless_encoder(**overrides)
        logger.info(f"Video Lossless Encoder: {lossless_encoder.__name__}")

        if post_filterchain_func is not None and not callable(post_filterchain_func):
            raise TypeError("VideoEncoder.video_lossless_encoder: post_filtering_func must be callable.")

        self.post_filterchain_func = post_filterchain_func
        logger.info("Post-filtering function set.")
