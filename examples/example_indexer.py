from svsfunc import Indexer, EpisodeInfo
from vardautomation import PresetWEB, PresetAAC

path = "/path/to/your/file.ext"

# simple indexer that return as VideoNode
lsmas = Indexer.lsmas()

# return the same thing, lsmas(path) will call lsmas.index(path) internally
clip = lsmas(path)
clip = lsmas.index(path)

# returns a FileInfo object
# lsmas is callable so it can be used where only functions are allowed
file_info = Indexer.file_info(trims_or_dfs=(24, -24), idx=lsmas, preset=[PresetWEB, PresetAAC])
file = file_info(path)


ep = EpisodeInfo(path, ep_num=1, op_range=None, ed_range=(30000, 32000), indexer=file_info)

ep.clip  # vs.VideoNode
ep.file  # FileInfo
ep.get_op()  # will raise an exception because ep does not have an op range set
ep.get_ed()  # will return ep.clip[30000:32001]


ep2 = EpisodeInfo(path, ep_num=2, op_range=(2000, 4200), ed_range=(30000, 32000), indexer=lsmas)

ep.clip  # vs.VideoNode
ep.file  # will raise an exception because lsmas only returns a VideoNode
