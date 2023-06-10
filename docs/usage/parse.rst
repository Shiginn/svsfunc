Using svsfunc.parse
===================

ParseBD
-------
ParseBD will try to parse the .mpls files in the BDMV to extract the list of the episodes in the correct order. To do so, you can specify the path to the BDMV folder (it will try to find every volumes present in this folder and subfolders) or give the path to every BD volume.
Use the ``ep_playlist`` parameters to select the playlist file to parse. In most BD, the correct playlist file is ``00000.mpls`` or ``00001.mpls``. In this exemple, it will use the playlist file ``00000.mpls`` (``ep_playlist=0``).

The indexer used can be configured using :py:class:`svsfunc.indexer.Indexer`.

.. code:: python

    from vardautomation import PresetBDWAV64, PresetOpus

    idx = Indexer.file_info2(trims_or_dfs=(24, -24), idx=Indexer.lsmas(), preset=[PresetBDWAV64, PresetOpus])
    BDMV = ParseBD("/path/to/BDMV", ep_playlist=0, indexer=idx)


.. code:: python

    from vardautomation import PresetBDWAV64, PresetOpus

    idx = Indexer.file_info2(trims_or_dfs=(24, -24), idx=Indexer.lsmas(), preset=[PresetBDWAV64, PresetOpus])
    BDMV = ParseBD("/path/to/BDMV", ep_playlist=0, indexer=idx)

You can set the range of the OP/ED of each episode with the ``set_op_ed_ranges`` method. Use ``None`` if the episode does not have an OP/ED.

.. code:: python

    BDMV.set_op_ed_ranges(
        op_ranges=[
            None
            (504, 2658),
            ...
        ],
        ed_ranges=[
            (30688, 32844),
            (30687, 32843),
            ...
        ]
    )

You can also set the NCOP and NCED of each episode with ``set_ncs``. Use a tuple for a range of episode or an int for a specific episode. Can be a path or a clip or ``None``.

.. code:: python

    BDMV.set_ncs(
        ncops={
            (1, 12): "/path/to/ncop1.m2ts",
            (13, 24): "/path/to/ncop2.m2ts"
        },
        nceds={
            (1, 12): "/path/to/nced1.m2ts",
            13: None,
            (14, 24): Indexer.lsmas("/path/to/nced2.m2ts")[24:]
        }
    )


To get an episode, use the ``get_episode`` method. The index start at 1, so doing ``BDMV.get_episode(1)`` will return episode 1.
``get_episode`` will return an :py:class:`svsfunc.indexer.EpisodeInfo` object with the corresponding episode number, OP/ED ranges (if set) and NCOP/NCED (if set).

To get the list of chapters of an episode, use the ``get_chapter`` method.

.. code:: 

    ep_01 = BDMV.get_episode(1)  # type -> EpisodeInfo[FileInfo2]
    ep_01_chapters = BDMV.get_chapter(1)  # type -> list[int]


ParseFolder
-----------
ParseFolder will try to get the list of files that matches an expression in the specified folder. Its main usage is for WEB release.

.. code:: python

    from vardautomation import PresetWEB, PresetAAC
    
    idx = Indexer.file_info(trims_or_dfs=(24, -24), idx=Indexer.lsmas(), preset=[PresetWEB, PresetAAC])
    WEB = ParseFolder("/path/to/folder", episode_pattern="* Anime Name S??E?? *.mkv", indexer=idx)


The episodes will be in the same order as the files in folder (sorted by name). So if your episodes don't have the same naming convention, it can impact the episode order. To fix this issue:

.. code:: 

    WEB.episodes = WEB.episodes[-4:] + WEB.episodes[0:-4] 

This will take the 4 last episodes and place them at the beginning of the list.


Just like ParseBD, you can get an episode with ``get_episode`` and set the OP/ED ranges with ``set_op_ed_ranges`` and NCOP/NCED with ``set_ncs``.

.. code:: 

    ep_01 = WEB.get_episode(1)  # Type is EpisodeInfo[FileInfo2]