__all__ = ["Encoder"]

from typing import List, NoReturn, Sequence, Tuple, TypeVar

from vardautomation import (
    UNDEFINED, AnyPath, AudioTrack, ChaptersTrack, FileInfo2, Lang, MatroskaFile, RunnerConfig, SelfRunner, Track,
    VideoTrack, VPath, logger
)

from .tooling.audio import AudioTooling
from .tooling.chapters import ChapterTooling
from .tooling.utils import UtilsTooling
from .tooling.video import VideoTooling

T = TypeVar("T")


class Encoder(VideoTooling, AudioTooling, ChapterTooling, UtilsTooling):
    """Generate an encoding chain"""
    mux: MatroskaFile | None = None
    runner: SelfRunner

    def muxer(
        self,
        v_title: str | None = None,
        a_title: str | List[str | None] | None = None,
        a_lang: Lang | List[Lang] = UNDEFINED,
        external_audio: List[AnyPath | Tuple[AnyPath, str | None, Lang]] | None = None,
        audio_tracks_order: List[int] | None = None,
        *muxer_overrides: str
    ) -> None:
        """
        Set parameters for the muxer.

        :param v_title:             Video track name.
        :param a_title:             Audio track(s) name(s).
        :param a_lang:              Audio track(s) language(s).
        :param external_audio:      Add external audio tracks. Can be a list of path, or a list of tuple
                                    (path, track_name, track_lang).
        :param audio_track_order:   Change audio track order on ouput file. Uses same indexes as AudioEncoder.set_tracks
                                    If external audios are added, the track number is defined as max(current_tracks) + 1
        :param muxer_options:       Additional paramters to be passed to the muxer.
        """

        if not isinstance(a_title, List):
            a_title = [a_title] * self.track_number
        else:
            a_title = self.ensure_size(a_title, self.track_number, "Encoder.muxer (a_title)")

        if not isinstance(a_lang, List):
            a_lang = [a_lang] * self.track_number
        else:
            a_lang = self.ensure_size(a_lang, self.track_number, "Encoder.muxer (a_lang)")

        logger.info(f"Muxing video file: {self.file.name_clip_output} (track name: {v_title})")
        tracks: List[Track] = [VideoTrack(self.file.name_clip_output, v_title)]

        a_tracks = list[AudioTrack]()

        if self.output_tracks:
            a_srcs = list(zip(self.output_tracks, a_title, a_lang))
            file_track = self._select_a_track()
            for idx, name, lang in a_srcs:
                logger.info(f"Muxing audio track {idx} (track name: {name}, track lang: {lang.name}-{lang.iso639})")
                a_tracks.append(AudioTrack(file_track.set_track(idx), name, lang))

        if external_audio is not None:
            for track in external_audio:
                self.track_number += 1
                self.input_tracks.append(max(self.input_tracks) + 1)  # [2, 4] ->  [2, 4, 5]
                self.output_tracks.append(max(self.output_tracks) + 1)

                if not isinstance(track, tuple):
                    track = (track, None, UNDEFINED)

                path, name, lang = track
                logger.info(f"Muxing audio file {path} (track name: {name}, track lang: {lang.name}-{lang.iso639})")
                a_tracks.append(AudioTrack(path, name, lang))

        if audio_tracks_order is not None:
            if len(audio_tracks_order) != self.track_number:
                raise ValueError("Encoder.muxer: missing audio tracks in audio_tracks_order.")

            logger.info(f"Output track order : {audio_tracks_order}")
            self.output_tracks = audio_tracks_order

        tracks += [a_tracks[i - 1] for i in self.output_tracks]

        if self.file.chapter:
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

        if self.a_encoder and isinstance(self.file, FileInfo2):
            for file in (self.file.a_src_cut.set_track(i) for i in self.input_tracks if self.file.a_src_cut):
                self.runner.work_files.add(file)

        if self.post_filterchain_func is not None:
            self.runner.plp_function = self.post_filterchain_func

        if self.qp_file is not None:
            self.runner.inject_qpfile_params(self.qp_file)

        self.runner.run()


    def clean_up(
        self,
        add_file: AnyPath | Sequence[AnyPath] | None = None,
        ignore_file: VPath | Sequence[VPath] | None = None
    ) -> None:
        """
        Delete temp files created by the encoder such as file.a_src/file.a_src_cut/file.a_enc_cut.

        :param add_file:        Additional files to delete.
        :param ignore_file:     Files that should not be deleted.
        """

        if not hasattr(self, "runner"):
            logger.error("Runner not found", False)

        if add_file is None:
            add_file = []
        elif not isinstance(add_file, Sequence):
            add_file = [add_file]

        if ignore_file is None:
            ignore_file = []
        elif not isinstance(ignore_file, Sequence):
            ignore_file = [ignore_file]

        for add in add_file:
            self.runner.work_files.add(add)
            logger.info(f"Adding {add} to workfiles")

        for ignore in ignore_file:
            self.runner.work_files.remove(ignore)
            logger.info(f"Removing {ignore} from workfiles")

        for file in sorted(self.runner.work_files):
            logger.info(f"Removing file {file}")

        self.runner.work_files.clear()


    def _select_a_track(self) -> VPath | NoReturn:
        """Returns audio track that matches audio tooling."""
        tracks = (self.file.a_enc_cut, self.file.a_src_cut, self.file.a_src)
        a_tools = (self.a_encoder, self.a_cutter, self.a_extracter)

        for track, tool in zip(tracks, a_tools):
            if track is not None and tool is not None:
                return track

        raise ValueError("Encoder._select_a_track: could not select audio from source file")


    @staticmethod
    def ensure_size(lst: List[T], max_size: int, source: str) -> NoReturn | List[T]:
        input_size = len(lst)

        if input_size > max_size:
            raise ValueError(f"{source}: Too many elements")
        elif input_size < max_size:
            return lst + [lst[-1]] * (max_size - input_size)
        else:
            return lst
