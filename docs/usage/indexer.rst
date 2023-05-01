Using svsfunc.indexer
=====================

Indexer
-------

The indexer class represent a pre-configured indexer that can be passed to other functions for easy use.
To index a file you can use the ``index`` method. Indexers are also callable.

.. code:: python

    idx = ...
    clip = idx.index("/path/to/file.ext")
    clip2 = idx("/path/to/file2.ext")


To configure an indexer, you can use the corresponding classmethod. The method will list all of the parameters of the indexer (except for file path)

.. code:: python

    from vardautomation import PresetWEB, PresetAAC

    idx = Indexer.lsmas()  # lsmas with default settings
    idx = Indexer.file_info(
        trims_or_dfs=(24, -24),
        preset=[PresetWEB, PresetAAC],
        idx=Indexer.lsmas()  # indexers are callable so they can replace standard indexing functions
    )

The available indexers are :

* `LSMAS <https://github.com/AkarinVS/L-SMASH-Works>`_
* `ffms2 <https://github.com/FFMS/ffms2>`_
* `BestSource <https://github.com/vapoursynth/bestsource>`_
* `DGIndexNV <https://www.rationalqm.us/dgdecnv/dgdecnv.html>`_
* `FileInfo/FileInfo2 <https://github.com/Ichunjo/vardautomation>`_


EpisodeInfo
-----------

``EpisodeInfo`` is a class that is useful to represent an episode with its number and its OP/ED ranges.

To index a file with ``EpisodeInfo``, you need to provide the path to the file and the number of the episode. OP and ED ranges are optional since some episode do not have OP/ED.
You can also configure the indexer using the ``Indexer`` class. The default indexer is :py:meth:`svsfunc.indexer.Indexer.lsmas`

.. code:: python

    ep = EpisodeInfo("/path/to/file", ep_num=1, op_range=None, ed_range=(30000, 32000), indexer=idx)

``EpisodeInfo`` will determine the type of the indexer object from the indexer used.
The instance has two property that allows you to access the indexed object : 

* ``file``: to access the FileInfo object (will error if you don't use :py:meth:`svsfunc.indexer.Indexer.file_info` or :py:meth:`svsfunc.indexer.Indexer.file_info2`)

* ``clip``: to access the VideoNode object (returns ``clip_cut`` if you use :py:meth:`svsfunc.indexer.Indexer.file_info` or :py:meth:`svsfunc.indexer.Indexer.file_info2`)

You can also access the OP and ED with the ``get_op`` and ``get_ed`` methods. If the range is ``None``, theses methods will raise an exception.
These methods can take a ``vs.VideoNode`` as an argument and will trim the given clip instead of the indexed clip.