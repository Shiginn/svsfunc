from svsfunc import ParseBD, ParseFolder, Indexer
from typing import reveal_type
from vardautomation import PresetBDWAV64, PresetOpus, PresetWEB, PresetAAC


# Creating a preconfigured FileInfo(2) indexer. Theses settings will be used to index every episode (can be overriden
# for specific episodes)
file_info_idx = Indexer.file_info(idx=Indexer.lsmas(), preset=[PresetWEB, PresetAAC])
file_info2_idx = Indexer.file_info2(trims_or_dfs=(24, -24), idx=Indexer.lsmas(), preset=[PresetBDWAV64, PresetOpus])

# Parsing the BDMV with chosen indexer
SRC = ParseFolder("/path/to/folder", pattern="* Series Name - S??E?? *.ext", indexer=file_info_idx)
SRC = ParseBD("/path/to/bdmv", indexer=file_info2_idx)

SRC.set_op_ed_ranges([None, (10, 2200)], [None, (30000, 32000)])

ep1 = SRC.get_episode(1)
ep1_chapters = SRC.get_chapter(1)  # will only work with ParseBD

ep2 = SRC.get_episode(2, trims_or_dfs=(0, -24))  # for this epiosde only, trims_or_dfs=(0, -24)

# ParseFolder: Type of "ep1" is "EpisodeInfo[FileInfo]"
# ParseBD: Type of "ep1" is "EpisodeInfo[FileInfo2]"
reveal_type(ep1)

ep1.clip  # vs.VideoNode
ep1.file  # FileInfo2 if ParseBD / FileInfo if ParseFolder
