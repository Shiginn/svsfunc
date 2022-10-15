__all__ = ["AudioTooling"]

from typing import Any, Dict, List, Tuple, Type, Union

from vardautomation import (
    Eac3toAudioExtracter, EztrimCutter, FFmpegAudioExtracter, FlacEncoder, MKVAudioExtracter, OpusEncoder,
    PassthroughAudioEncoder, PassthroughCutter, PresetWEB, QAACEncoder, ScipyCutter, SoxCutter, logger
)

from .base import BaseEncoder

AudioExtracters = Union[FFmpegAudioExtracter, MKVAudioExtracter, Eac3toAudioExtracter]
AudioCutters = Union[EztrimCutter, SoxCutter, ScipyCutter, PassthroughCutter]
AudioEncoders = Union[FlacEncoder, OpusEncoder, QAACEncoder, PassthroughAudioEncoder]
AudioExtractersType = Type[AudioExtracters]
AudioCuttersType = Type[AudioCutters]
AudioEncodersType = Type[AudioEncoders]


class AudioTooling(BaseEncoder):
    """Tools for audio extracting/cutting and encoding"""

    track_number: int = 0
    input_tracks: List[int] = []
    output_tracks: List[int] = []
    a_extracter: List[AudioExtracters] | None = None
    a_cutter: List[AudioCutters] | None = None
    a_encoder: List[AudioEncoders] | None = None


    def set_tracks(self, tracks: int | List[int] | None) -> None:
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
        extracter: AudioExtractersType,
        global_settings: Dict[str, Any] | None = None,
        overrides: List[Tuple[int, Dict[str, Any]]] | None = None
    ) -> None:
        """
        Set the audio extracter that will be used. Not needeed if you use FileInfo2.

        :param extracter:           Audio extracter to use.
        :param global_settings:     Settings that will be passed to every track.
        :param overrides:           Override global settings for specific tracks. Format is (track_number, settings).
        """
        # eac3to index start at 1 while others are zero based
        if extracter == Eac3toAudioExtracter:
            self.input_tracks = [t + 1 for t in self.input_tracks]

        extracter_list = [extracter] * self.track_number
        settings = self._get_settings(global_settings, overrides, self.get_func_name())

        self.a_extracter = []
        for ext_t, in_idx, out_idx, setting in zip(extracter_list, self.input_tracks, self.output_tracks, settings):
            self.a_extracter.append(ext_t(self.file, track_in=in_idx, track_out=out_idx, **setting))

        logger.info(f"Audio Extracter: {extracter.__name__}")
        logger.info(f"Overrides: {overrides}")


    def audio_cutter(
        self,
        cutter: AudioCuttersType,
        global_settings: Dict[str, Any] | None = None,
        overrides: List[Tuple[int, Dict[str, Any]]] | None = None
    ) -> None:
        """
        Set the audio cutter that will be used. Not needeed if you use FileInfo2.

        :param cutter:              Audio cutter to use.
        :param global_settings:     Settings that will be passed to every track.
        :param overrides:           Override global settings for specific tracks. Format is (track_number, settings).
        """
        cutter_list = [cutter] * self.track_number
        settings = self._get_settings(global_settings, overrides, self.get_func_name())

        self.a_cutter = []
        for cutter_t, out_idx, setting in zip(cutter_list, self.output_tracks, settings):
            self.a_cutter.append(cutter_t(self.file, track=out_idx, **setting))

        logger.info(f"Audio Cutter: {cutter.__name__}")
        logger.info(f"Overrides: {overrides}")



    def audio_encoder(
        self,
        encoder: AudioEncodersType,
        global_settings: Dict[str, Any] | None = None,
        overrides: List[Tuple[int, Dict[str, Any]]] | None = None
    ) -> None:
        """
        Set the audio encoder that will be used.

        :param encoder:             Audio encoder to use.
        :param global_settings:     Settings that will be passed to every track.
        :param overrides:           Override global settings for specific tracks. Format is (track_number, settings).
        """
        func_name = self.get_func_name()

        if PresetWEB in self.file.preset:
            raise ValueError(f"AudioEncoder.{func_name}: cannot set audio_encoder when using PresetWEB.")

        encoder_list = [encoder] * self.track_number
        settings = self._get_settings(global_settings, overrides, func_name)

        self.a_encoder = []
        for encoder_t, out_idx, setting in zip(encoder_list, self.output_tracks, settings):
            self.a_encoder.append(encoder_t(self.file, track=out_idx, **setting))

        logger.info(f"Audio Encoder: {encoder.__name__}")
        logger.info(f"Overrides: {overrides}")


    def _get_settings(
        self, global_settings: Dict[str, Any] | None,
        overrides: List[Tuple[int, Dict[str, Any]]] | None,
        func: str
    ) -> List[Dict[str, Any]]:

        if global_settings is None:
            global_settings = dict[str, Any]()

        settings = [global_settings] * self.track_number

        if overrides:
            if len(overrides) > self.track_number:
                raise ValueError(f"AudioEncoder.{func}: too many overrides")

            overrides = sorted(overrides)

            for i, track in enumerate(self.input_tracks):
                override_track, override_settings = overrides[0]
                if track == override_track:
                    settings[i] = override_settings
                    overrides.pop(0)

                    if not overrides:
                        break

        return settings
