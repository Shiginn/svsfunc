Using svsfunc.episode_info
==========================

EpisodeInfo
-----------

``EpisodeInfo`` is a class that is useful to represent an episode with its number, its OP/ED ranges and its NCOP/NCED.

To index a file with ``EpisodeInfo``, you need to provide a ``VideoNode`` or a ``src_file`` (from ``vsmuxtools``) and the number of the episode. OP/ED ranges and NCOP/NCED are optional since some episode do not have OP/ED.

.. code:: python

    from svsfunc import EpisodeInfo
    from vsmuxtools import src_file

    clip = src_file("/path/to/file", trim=(24, None))

    ep = EpisodeInfo(
        clip,
        ep_num=1,
        op_range=None,
        ed_range=(30000, 32158),
        ncop=None,
        nced=core.ffms2.Source("path/to/nced")[24:-24],
    )

To access the source clip, you can use:

* :py:attr:`svsfunc.episode_info.EpisodeInfo.src` to get the raw source clip.
* :py:attr:`svsfunc.episode_info.EpisodeInfo.src_cut` to get the source clip trimmed (``vsmuxtools.src_file`` only).
* :py:meth:`svsfunc.episode_info.EpisodeInfo.init` to get the source clip initialized with ``vstools.initialize_clip``.
* :py:meth:`svsfunc.episode_info.EpisodeInfo.init_cut` to get the source clip trimmed and initialized with ``vstools.initialize_clip`` (``vsmuxtools.src_file`` only).

You can also access the OP and ED with the :py:meth:`svsfunc.episode_info.EpisodeInfo.get_op` and :py:meth:`svsfunc.episode_info.EpisodeInfo.get_ed` methods. If the range is ``None``, theses methods will raise an exception.
These methods can take a ``vs.VideoNode`` as an argument and will trim the OP/ED from the given clip instead of :py:attr:`svsfunc.episode_info.EpisodeInfo.src_cut`.

You can also access the NCOP and NCED with the :py:meth:`svsfunc.episode_info.EpisodeInfo.get_ncop` and :py:meth:`svsfunc.episode_info.EpisodeInfo.get_nced` methods. By default, the clips will be trimmed to match the frame count of the OP or ED frame count (if range is specified). This behaviour can be disabled with the ``trim_nc*`` parameter.

Finally, you can generate a 0-padded episode number string using :py:meth:`svsfunc.episode_info.EpisodeInfo.ep_num_str`.