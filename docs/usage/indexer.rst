Using svsfunc.indexer
=====================

Indexer
-------

The available indexers are :

* `L-SMASH-Works <https://github.com/AkarinVS/L-SMASH-Works>`_
* `DGIndexNV <https://www.rationalqm.us/dgdecnv/dgdecnv.html>`_
* `ffms2 <https://github.com/FFMS/ffms2>`_
* `BestSource <https://github.com/vapoursynth/bestsource>`_ (audio and video)
* `FileInfo/FileInfo2 <https://github.com/Ichunjo/vardautomation>`_


To configure an indexer, you use the parameters of the :py:meth:`~svsfunc.indexer.Indexer.__init__` method.

.. code:: python

    from svsfunc import LSMAS, SrcFile

    idx = LSMAS()  # lsmas with default settings

    idx = SrcFile(trims=(24, -24), idx=DGIndexNV())

To index a file, you just to call the :py:meth:`~svsfunc.indexer.Indexer.index` method with the path of the file. Indexers are also callable.
You can also override the default settings of the indexer.

.. code:: python

    from svsfunc import LSMAS()

    idx = LSMAS()
    clip = idx.index("/path/to/file.ext")
    clip2 = idx("/path/to/file2.ext", cache=False)


EpisodeInfo
-----------

``EpisodeInfo`` is a class that is useful to represent an episode with its number, its OP/ED ranges and its NCOP/NCED.

To index a file with ``EpisodeInfo``, you need to provide the path to the file and the number of the episode. OP/ED ranges and NCOP/NCED are optional since some episode do not have OP/ED.
You can also configure the indexer with the ``indexer`` parameter (the default is :py:class:`~svsfunc.indexer.LSMAS`).

.. code:: python

    from svsfunc import EpisodeInfo, LSMAS

    idx = LSMAS()

    ep = EpisodeInfo(
        "/path/to/file",
        ep_num=1,
        op_range=None,
        ed_range=(30000, 32158),
        ncop=None,
        nced=idx("path/to/nced")[24:-24],
        indexer=idx
    )

``EpisodeInfo`` will determine the type of the indexer object from the indexer used.
The instance has two property that allows you to access the indexed object : 

* ``src_file``: to access the SrcFile object (will error if you don't use :py:class:`~svsfunc.indexer.SrcFile`)

* ``clip``: to access the VideoNode object (returns ``clip_cut`` if you use :py:class:`~svsfunc.indexer.SrcFile`)

You can also access the OP and ED with the ``get_op`` and ``get_ed`` methods. If the range is ``None``, theses methods will raise an exception.
These methods can take a ``vs.VideoNode`` as an argument and will trim the given clip instead of the indexed clip.