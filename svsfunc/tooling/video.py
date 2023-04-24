from __future__ import annotations

__all__ = ["VideoTooling"]

from typing import Any, Callable

import vapoursynth as vs
from vardautomation import VPath, logger

from ..custom_types import EncoderTypes
from .base import BaseEncoder


class VideoTooling(BaseEncoder):
    """Tools for video encoding"""

    v_encoder: EncoderTypes.Video.Encoder
    v_lossless_encoder: EncoderTypes.Video.LosslessEncoder | None = None

    qp_file: vs.VideoNode | None = None
    post_filterchain_func: Callable[[VPath], vs.VideoNode] | None = None

    def video_encoder(
        self,
        encoder: type[EncoderTypes.Video.Encoder],
        settings: str | list[str] | dict[str, Any],
        resumable: bool = False,
        zones: dict[tuple[int, int], dict[str, Any]] | None = None,
        prefetch: int = 0,
        qp_file: bool | vs.VideoNode | None = None,
        **enc_overrides: Any
    ) -> None:
        """
        Set the video encoder.

        :param encoder:         Encoder to use.
        :param settings:        Video encoder settings.
        :param resumable:       Allow encoding to be paused and resumed.
        :param zones:           Custom zone ranges.
        :param prefetch:        Max number of concurrent rendered frames
        :param qp_file:         Generate qp file from clip. If True, will use `file.clip_cut`.
                                Custom clip can also be used.
        :param enc_overrides:   Additional paramters to be passed to the encoder.
        """
        if zones is not None and resumable:
            logger.warning("Zones are not shifted when encode is resumed. This may lead to incorrect zones.")

        self.v_encoder = encoder(settings, zones=zones, **enc_overrides)
        self.v_encoder.resumable = resumable
        self.v_encoder.prefetch = prefetch

        logger.info(f"Video Encoder: {encoder.__name__}")
        logger.info(f"Zones: {zones}")

        if isinstance(qp_file, vs.VideoNode):
            self.qp_file = qp_file  # type: ignore  # wtf mypy ?
            logger.info("Using custom VideoNode for qp_file")
        elif qp_file:
            self.qp_file = self.file.clip_cut
            logger.info("Using file.clip_cut for qp_file")


    def video_lossless_encoder(
        self, lossless_encoder: type[EncoderTypes.Video.LosslessEncoder],
        post_filterchain_func: Callable[[VPath], vs.VideoNode] | None = None,
        **enc_overrides: Any
    ) -> None:
        """
        Set lossless video encoder.

        :param lossless_encoder:        Encoder to use.
        :param post_filterchain_func:   Function to be run after filterchain and before encoding.
        :param enc_overrides:           Addition parameters to be passed to the encoder.
        """
        self.v_lossless_encoder = lossless_encoder(**enc_overrides)
        logger.info(f"Video Lossless Encoder: {lossless_encoder.__name__}")

        if post_filterchain_func is not None and not callable(post_filterchain_func):
            raise TypeError("VideoEncoder.video_lossless_encoder: post_filtering_func must be callable.")

        self.post_filterchain_func = post_filterchain_func
        if self.post_filterchain_func:
            logger.info("Post-filtering function set.")
