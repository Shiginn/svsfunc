__all__ = ["AudioTooling"]

from typing import Any, NoReturn

from vardautomation import Eac3toAudioExtracter, PresetWEB, logger

from ..custom_types import EncoderTypes
from .base import BaseEncoder


class AudioTooling(BaseEncoder):
    """Tools for audio extracting/cutting and encoding"""

    track_number: int = 0
    input_tracks: list[int] = []
    output_tracks: list[int] = []
    a_extracter: list[EncoderTypes.Audio.Extracter] | None = None
    a_cutter: list[EncoderTypes.Audio.Cutter] | None = None
    a_encoder: list[EncoderTypes.Audio.Encoder] | None = None


    def set_audio_tracks(self, tracks: int | list[int] | None) -> None:
        """
        Set the tracks that will be processed by the audio extracter/cutter/encoder. The first audio tracks is track
        number 1, things might broke if you source has more than one video track. Track order is not preserved.

        :param tracks:  Tracks to process.
        """
        self.input_tracks = ([tracks] if isinstance(tracks, int) else sorted(tracks)) if tracks is not None else []
        self.output_tracks = self.input_tracks.copy()
        self.track_number = len(self.input_tracks)

        logger.info(f"Processing audio tracks: {', '.join(str(t) for t in self.input_tracks)}")


    def audio_extracter(
        self,
        extracter: type[EncoderTypes.Audio.Extracter],
        global_settings: dict[str, Any] | None = None,
        overrides: dict[int, dict[str, Any]] | None = None
    ) -> None:
        """
        Set the audio extracter that will be used. Not needeed if you use FileInfo2.

        :param extracter:           Audio extracter to use.
        :param global_settings:     Settings that will be passed to every track.
        :param overrides:           Override global settings for specific tracks. Format is a dict where key is the
                                    track to override and value is a dict of settings.
        """
        func_name = self.get_func_name()
        self._check_tracks(func_name)

        # eac3to index start at 1 while others are zero based
        a_tracks = [t + 1 for t in self.input_tracks] if extracter == Eac3toAudioExtracter else self.input_tracks

        extracter_list = [extracter] * self.track_number
        settings = self._get_settings(global_settings, overrides, self.get_func_name())

        self.a_extracter = []
        for ext_t, in_idx, out_idx, setting in zip(extracter_list, a_tracks, self.output_tracks, settings):
            self.a_extracter.append(ext_t(self.file, track_in=in_idx, track_out=out_idx, **setting))

        logger.info(f"Audio Extracter: {extracter.__name__}")
        logger.info(f"Overrides: {overrides}")


    def audio_cutter(
        self,
        cutter: type[EncoderTypes.Audio.Cutter],
        global_settings: dict[str, Any] | None = None,
        overrides: dict[int, dict[str, Any]] | None = None
    ) -> None:
        """
        Set the audio cutter that will be used. Not needeed if you use FileInfo2.

        :param cutter:              Audio cutter to use.
        :param global_settings:     Settings that will be passed to every track.
        :param overrides:           Override global settings for specific tracks. Format is a dict where key is the
                                    track to override and value is a dict of settings.
        """
        func_name = self.get_func_name()
        self._check_tracks(func_name)

        cutter_list = [cutter] * self.track_number
        settings = self._get_settings(global_settings, overrides, self.get_func_name())

        self.a_cutter = []
        for cutter_t, out_idx, setting in zip(cutter_list, self.output_tracks, settings):
            self.a_cutter.append(cutter_t(self.file, track=out_idx, **setting))

        logger.info(f"Audio Cutter: {cutter.__name__}")
        logger.info(f"Overrides: {overrides}")



    def audio_encoder(
        self,
        encoder: type[EncoderTypes.Audio.Encoder],
        global_settings: dict[str, Any] | None = None,
        overrides: dict[int, dict[str, Any]] | None = None
    ) -> None:
        """
        Set the audio encoder that will be used.

        :param encoder:             Audio encoder to use.
        :param global_settings:     Settings that will be passed to every track.
        :param overrides:           Override global settings for specific tracks. Format is a dict where key is the
                                    track to override and value is a dict of settings.
        """
        func_name = self.get_func_name()
        self._check_tracks(func_name)

        if PresetWEB in self.file.preset:
            raise ValueError(f"AudioEncoder.{func_name}: cannot set audio_encoder when using PresetWEB.")

        encoder_list = [encoder] * self.track_number
        settings = self._get_settings(global_settings, overrides, func_name)

        self.a_encoder = []
        for encoder_t, out_idx, setting in zip(encoder_list, self.output_tracks, settings):
            self.a_encoder.append(encoder_t(self.file, track=out_idx, **setting))

        logger.info(f"Audio Encoder: {encoder.__name__}")
        logger.info(f"Overrides: {overrides}")


    def _check_tracks(self, func_name: str) -> None | NoReturn:
        if self.track_number == 0:
            raise ValueError(
                f"AudioEncoder.{func_name}: no audio track set. Use AudioEncoder.set_audio_tracks before running " +
                f"AudioEncoder.{func_name}"
            )
        return None


    def _get_settings(
        self, global_settings: dict[str, Any] | None,
        overrides: dict[int, dict[str, Any]] | None,
        func: str
    ) -> list[dict[str, Any]]:

        if global_settings is None:
            global_settings = dict[str, Any]()

        settings = [global_settings.copy() for _ in range(self.track_number)]

        if overrides is None:
            return settings

        if len(overrides) > self.track_number:
            raise ValueError(f"AudioEncoder.{func}: too many overrides")


        for i, track in enumerate(self.input_tracks):
            if track in overrides:
                settings[i] |= overrides[track]

        return settings
