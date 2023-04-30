from vardautomation import (
    JAPANESE, X265, Eac3toAudioExtracter, EztrimCutter, OpusEncoder, PresetBDWAV64, PresetOpus
)
from vstools import vs, initialize_clip, finalize_clip
from svsfunc import Encoder, Indexer


def filterchain(clip: vs.VideoNode) -> vs.VideoNode:
    src = initialize_clip(clip)

    # filtering here

    return finalize_clip(src)


src = Indexer.file_info(trims_or_dfs=(24, -24), preset=[PresetBDWAV64, PresetOpus]).index("/path/to/src.ext")
filtered = filterchain(src.clip_cut)

enc = Encoder(src, filtered)

enc.video_encoder(X265, "/path/to/settings", resumable=True)

enc.set_audio_tracks([1, 2])
enc.audio_extracter(Eac3toAudioExtracter)
enc.audio_cutter(EztrimCutter)
enc.audio_encoder(OpusEncoder, global_settings=dict(bitrate=96 * 2), overrides={2: dict(bitrate=96 * 6)})  # 1st track is 2.0, 2nd track is 5.1  # noqa: E501

enc.muxer("x265 BD", ["Opus 2.0", "Opus 5.1"], JAPANESE)
enc.run()

enc.make_comp()
enc.generate_keyframes()
enc.clean_up()
