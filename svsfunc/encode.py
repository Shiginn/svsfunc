from __future__ import annotations

__all__ = ["Encoder"]

from typing import NoReturn, Sequence

from vardautomation import (
    UNDEFINED, AnyPath, AudioTrack, ChaptersTrack, Eac3toAudioExtracter, FileInfo2, Lang, MatroskaFile, RunnerConfig,
    SelfRunner, Track, VideoTrack, VPath, logger
)
from vardautomation.vpathlib import CleanupSet
from vstools import to_arr

from .tooling.audio import AudioTooling
from .tooling.chapters import ChapterTooling
from .tooling.utils import UtilsTooling
from .tooling.video import VideoTooling
from .utils import normalize_list


class Encoder(VideoTooling, AudioTooling, ChapterTooling, UtilsTooling):
    """Generate an encoding chain"""
    external_audio: list[VPath] = []
    mux: MatroskaFile | None = None
    runner: SelfRunner | None = None

    def muxer(
        self,
        v_title: str | None = None,
        a_title: str | list[str | None] | None = None,
        a_lang: Lang | list[Lang] = UNDEFINED,
        external_audio: list[AnyPath | AudioTrack] | None = None,
        audio_tracks_order: list[int] | None = None,
        *muxer_overrides: str
    ) -> None:
        """
        Set parameters for the muxer.

        :param v_title:             Video track name.
        :param a_title:             Audio track(s) name(s).
        :param a_lang:              Audio track(s) language(s).
        :param external_audio:      Add external audio tracks. Can be a list of path, or a list of AudioTrack.
        :param audio_track_order:   Change audio track order on ouput file. Uses same indexes as
                                    AudioEncoder.set_input_tracks. If external audios are added, the track number is
                                    defined as max(current_tracks) + 1
        :param muxer_options:       Additional paramters to be passed to the muxer.
        """

        a_title = normalize_list(a_title, self.track_number, None, "Encoder.muxer (a_title)")
        a_lang = normalize_list(a_lang, self.track_number, UNDEFINED, "Encoder.muxer (a_lang)")

        logger.info(f"Muxing video file: {self.file.name_clip_output} (track name: {v_title})")
        tracks: list[Track] = [VideoTrack(self.file.name_clip_output, v_title)]

        a_tracks = list[AudioTrack]()

        # tracks extracted/cut/encoded from input file
        if self.input_tracks:
            file_track = self._select_a_track()
            for idx, name, lang in zip(self.input_tracks, a_title, a_lang):
                logger.info(f"Muxing audio track {idx} (track name: {name}, track lang: {lang.name}-{lang.iso639})")
                a_tracks.append(AudioTrack(file_track.set_track(idx), name, lang))

        # external tracks provided by user
        for track in (external_audio or []):
            if not isinstance(track, AudioTrack):
                track = AudioTrack(track, None, UNDEFINED)

            if not track.path.exists():
                raise ValueError(f"Encoder.muxer: external audio file {track.path.to_str()} does not exist.")

            self.track_number += 1
            a_tracks.append(track)
            self.external_audio.append(track.path)

            logger.info(f"Muxing audio file {track.path} (track name: {track.name}, track lang: {track.lang.name}-{track.lang.iso639})")  # noqa: E501

        # reordering tracks
        default_audio_order = list(range(1, self.track_number + 1))
        if audio_tracks_order is not None:
            if sorted(audio_tracks_order) != default_audio_order:
                raise ValueError(f"Encoder.muxer: invalid audio track order given, must be list of indices between 1 and {self.track_number}")  # noqa: E501

            logger.info(f"Output track order : {audio_tracks_order}")

        tracks += [a_tracks[i - 1] for i in audio_tracks_order or default_audio_order]

        # chapter file
        if self.file.chapter is not None and self.file.chapter.exists():
            logger.info(f"Muxing chapter file: {self.file.chapter}")
            tracks.append(ChaptersTrack(self.file.chapter))

        self.mux = MatroskaFile(self.file.name_file_final, tracks, *muxer_overrides)


    def run(self, order: RunnerConfig.Order = RunnerConfig.Order.VIDEO) -> None:
        """
        Start the encode with specified settings. Should be called after everything is configured.

        :param order:   Encode video or audio first (defaults to video).
        """
        if self.v_encoder is None:
            raise TypeError("Encoder.run: no video encoder set")

        config = RunnerConfig(
            v_encoder=self.v_encoder,
            v_lossless_encoder=self.v_lossless_encoder,
            a_extracters=self.a_extracter,
            a_cutters=self.a_cutter,
            a_encoders=self.a_encoder,
            mkv=self.mux,
            order=order,
        )

        self.runner = SelfRunner(self.clip, self.file, config)

        if self.post_filterchain_func is not None:
            self.runner.plp_function = self.post_filterchain_func

        if self.qp_file is not None:
            self.runner.inject_qpfile_params(self.qp_file)

        self.runner.run()

        # bug in vardautomation cause work files be inacurrate (can miss some files or have unwanted files)
        self.runner.work_files = CleanupSet([self.file.name_clip_output])
        if self.file.chapter:
            self.runner.work_files.add(self.file.chapter)

        if self.a_extracter:
            assert self.file.a_src

            for i in self.input_tracks:
                self.runner.work_files.add(self.file.a_src.set_track(i))

            if isinstance(self.a_extracter[0], Eac3toAudioExtracter):
                for i in self.input_tracks:
                    self.runner.work_files.add(self.file.a_src.set_track(i).append_stem(" - Log").with_suffix(".txt"))

        if self.a_cutter or (self.a_encoder and isinstance(self.file, FileInfo2)):
            assert self.file.a_src_cut
            for i in self.input_tracks:
                self.runner.work_files.add(self.file.a_src_cut.set_track(i))

        if self.a_encoder:
            assert self.file.a_enc_cut
            for i in self.input_tracks:
                self.runner.work_files.add(self.file.a_enc_cut.set_track(i))


    def clean_up(
        self,
        add_file: AnyPath | Sequence[AnyPath] | None = None,
        ignore_file: VPath | Sequence[VPath] | None = None,
        keep_external_audio: bool = True
    ) -> None | NoReturn:
        """
        Delete temp files created by the encoder such as file.a_src/file.a_src_cut/file.a_enc_cut.

        :param add_file:            Additional files to delete.
        :param ignore_file:         Files that should not be deleted.
        :param keep_external_audio  Do not delete external audio files used in Encoder.muxer (Default: True)
        """

        if self.runner is None:
            logger.error("No runner detected", False)

        add_file = to_arr(add_file) if add_file is not None else []
        ignore_file = to_arr(ignore_file) if ignore_file is not None else []

        if keep_external_audio:
            ignore_file += self.external_audio

        for add in add_file:
            self.runner.work_files.add(add)
            logger.info(f"Adding {add} to workfiles")

        for ignore in ignore_file:
            self.runner.work_files.remove(ignore)
            logger.info(f"Removing {ignore} from workfiles")

        for file in sorted(self.runner.work_files):
            logger.info(f"Deleted {file}")

        self.runner.work_files.clear()
        return None


    def _select_a_track(self) -> VPath | NoReturn:
        """Returns audio track that matches audio tooling."""
        tracks = (self.file.a_enc_cut, self.file.a_src_cut, self.file.a_src)
        a_tools = (self.a_encoder, self.a_cutter, self.a_extracter)

        for track, tool in zip(tracks, a_tools):
            if track is not None and tool is not None:
                return track

        raise ValueError("Encoder._select_a_track: could not select audio from source file")
