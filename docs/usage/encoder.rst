Using svsfunc.encode
=====================

.. note:: 
    In this exemple, we assume that ``clip`` is a ``VideoNode`` and ``file`` a ``FileInfo`` object.
    Also, make sure you use the correct presets with FileInfo.

To use this module, you need to start by creating an ``Encoder`` object.

.. code:: python
    
    from svsfunc import Encoder
    
    clip = ...
    file = ...
    
    encoder = Encoder(file, clip)

You can now add the different steps of you encoding chain.


Video
-----
Calling ``video_encoder()`` is required.

.. code:: python

    from vardautomation import X265, FFV1Encoder

    encoder.video_encoder(X265, settings="path/to/settings/file", resumable=True, qp_file=True)
    encoder.video_lossless_encoder(FFV1Encoder)


Audio
-----
In this exemple, we assume that our source has 2 audio tracks, the first one is 2.0 and the second one is 5.1.
If you are using ``FileInfo2``, you don't need to call ``audio_extracter`` and ``audio_cutter``.

.. code:: python

    from vardautomation import Eac3toAudioExtracter, EztrimCutter, OpusEncoder

    encoder.set_tracks([1, 2])

    # if file is FileInfo
    encoder.audio_extracter(Eac3toAudioExtracter)
    encoder.audio_cutter(EztrimCutter)

    encoder.audio_encoder(
        OpusEncoder,
        global_settings=dict(bitrate=2 * 96),
        overrides=(2, dict(bitrate=6 * 96))
    )



Chapters
--------
If you are working with Blu-Ray files, you can extract the chapters using vardautomation's ``MplsReader``.
Otherwise, you can use a list of integers where each number represent the first frame of a chapter.

.. code:: python

    from vardautomation import MplsReader

    chapters = MplsReader("path/to/bd/volume").get_playlist()[1].mpls_chapters[0].to_chapters()  # blu ray
    chapters = [0, 1200, 3700, 12500, 32000]  # web

    chapters_names = ["Intro", "OP", "Part A", "Part B", "ED"]

    encoder.make_chapters(chapters, chapters_names)


Muxing
------
You can set the language and title of each audio track. You can also import exteral audio tracks. If just the path is given, the track will have no title and the language will be undefined.

.. code:: python

    from vardautomation import ENGLISH, JAPANESE, FRENCH

    encoder.muxer(
        v_title="X265 BD by Encoder@Team",
        a_title=["Opus 2.0", "Opus 5.1"],
        a_lang=[JAPANESE, ENGLISH],
        external_audio=[("my/encoded/audio.opus", "Opus 5.1", FRENCH)]
    )


Running the encode
------------------
You can now run the encoder. You can use the ``clean_up`` method to delete all of the temp files generated during the encode.

.. code:: python

    encoder.run()
    encoder.clean_up()


Utilities
---------
Theses functions can be run whenever you want but make sure they have the required files available.

.. code:: python

    encoder.make_comp(num_frames=50)  # requires file.name_file_final
    encoder.generate_keyframes()