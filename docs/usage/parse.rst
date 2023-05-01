Using svsfunc.parse
===================

ParseBD
-------
ParseBD will try to parse the .mpls files in the BDMV to extract the list of the episodes in the correct order. To do so, you can specify the path to each BD volume or leave ``bd_volumes=None`` to try to find them automatically (they need to be in ``bdmv_folder`` directory).
The ``ep_playlist`` parameters can be used to change the playlist file to parse. In most BD, the correct playlist file is ``00001.mpls``. In this exemple, it will use the playlist file ``00000.mpls``.

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

To get an episode, use the ``get_episode`` method. The index start at 1, so doing ``BDMV.get_episode(1)`` will return episode 1.
``get_episode`` will return an :py:class:`svsfunc.indexer.EpisodeInfo` object with the corresponding episode number and OP/ED ranges (if set).

To get the list of chapters of an episode, use the ``get_chapter`` method.

.. code:: 

    ep_01 = BDMV.get_episode(1)  # type -> EpisodeInfo[FileInfo2]
    ep_01_chapters = BDMV.get_chapter(1)  # type -> list[Chapter]


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


Just like ParseBD, you can get an episode with ``get_episode`` and set the OP/ED ranges with ``set_op_ed_ranges``.

.. code:: 

    ep_01 = WEB.get_episode(1)  # Type is EpisodeInfo[FileInfo2]