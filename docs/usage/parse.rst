Using svsfunc.parse
===================

ParseBD
-------
ParseBD will try to parse the .mpls files in the BDMV to extract the list of the episodes in the correct order. To do so, you can specify the path to the BDMV folder (it will try to find every volumes present in this folder and subfolders) or give the path to every BD volume.
Use the ``ep_playlist`` parameters to select the playlist file to parse. In most BD, the correct playlist file is ``00000.mpls`` or ``00001.mpls``. In this exemple, it will use the playlist file ``00000.mpls`` (``ep_playlist=0``).
.

.. code:: python

    from svsfunc import ParseBD
    from vssource import BestSource

    BDMV = ParseBD("/path/to/BDMV", ep_playlist=0, indexer=lambda f: BestSource().source(f))



To get an episode, use the :py:meth:`svsfunc.parse.ParseBD.get_episode` method. The index start at 1, so doing ``BDMV.get_episode(1)`` will return episode 1.
:py:meth:`svsfunc.parse.ParseBD.get_episode` will return a ``VideoNode`` or a ``src_file``, depending on the indexer used, which can be passed to :py:class:`svsfunc.episode_info.EpisodeInfo` or used as is.

To get the list of chapters of an episode, use the :py:meth:`svsfunc.parse.ParseBD.get_chapter` method. A list of name can be passed to rename the chapters (default to Chapter 1, 2, 3...).
If you use ``src_file`` with trims, you can pass the it to also apply the trims on the chapters.

.. code:: 

    ep_01 = BDMV.get_episode(1)

    ep_01_chapters = BDMV.get_chapter(1)
    # or 
    ep_01_chapters = BDMV.get_chapter(1, ["Intro", "OP", "Part A", "Part B", "ED"])
    # or 
    ep_01_chapters = BDMV.get_chapter(1, [...], ep_01) # asuming ep_01 is of type vsmuxtools.src_file

ParseFolder
-----------
ParseFolder will try to get the list of files that matches an expression in the specified folder. Its main usage is for WEB release.

.. code:: python

    from svsfunc import ParseFolder
    from vssource import BestSource

    WEB = ParseFolder("/path/to/folder", pattern="* Anime Name S??E?? *.mkv", indexer=lambda f: BestSource().source(f))


The episodes will be in the same order as the files in folder (sorted by name). So if your episodes don't have the same naming convention, it can impact the episode order. To fix this issue:

.. code:: 

    WEB.episodes = WEB.episodes[-4:] + WEB.episodes[0:-4] 

This will take the 4 last episodes and place them at the beginning of the list.


Just like ParseBD, you can get an episode with :py:meth:`svsfunc.parse.ParseFolder.get_episode`:

.. code:: 

    ep_01 = WEB.get_episode(1)