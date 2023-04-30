from vardautomation import FileInfo, PresetBDWAV64, PresetOpus
from vstools import finalize_clip, initialize_clip, vs

from svsfunc import BaseFiltering, Encoder, EpisodeInfo, Indexer

idx = Indexer.file_info(idx=Indexer.lsmas(), preset=[PresetBDWAV64, PresetOpus])
ep = EpisodeInfo("/path/to/episode", 1, None, None, indexer=idx)


class MyFilterchain(BaseFiltering):
    episode: EpisodeInfo[FileInfo]

    def __init__(self, episode: EpisodeInfo[FileInfo]) -> None:
        self.episode = episode


    def filter(self) -> vs.VideoNode:
        src = initialize_clip(self.episode.clip)
        self.add_preview(src, "source")

        edge_fix = ...
        self.add_preview(edge_fix, "edge fix")

        denoise = ...
        self.add_preview(denoise, "denoise")

        ...

        grain = ...
        self.add_preview(grain, "grain")

        return finalize_clip(grain)


filterchain = MyFilterchain(ep)


if __name__ == "__main__":
    enc = Encoder(ep.file, filterchain.filter())
    ...

elif __name__ == "__vapoursynth__":
    filterchain.filter().set_output()

elif __name__ == "__vspreview":
    from lvsfunc import stack_planes

    filterchain.filter()
    filterchain.set_outputs(preview_func=stack_planes)
