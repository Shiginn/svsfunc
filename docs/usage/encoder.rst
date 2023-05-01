Using svsfunc.encode
=====================

The :py:class:`~svsfunc.encode.Encoder` allows you to automate the encoding process. To do so, it uses Vardautomation and the various tools it provides to encode, mux and create chapters.

The first step is to create an :py:class:`~svsfunc.encode.Encoder` object. You need a file (``FileInfo`` or ``FileInfo``) and a clip.

.. code:: python
    
    from svsfunc import Encoder
    
    clip = ...
    file = ...
    
    encoder = Encoder(file, clip)


Video
-----
You need to add a video encoder by calling :py:meth:`~svsfunc.tooling.video.VideoTooling.video_encoder`. You can also add a lossless video encoder. It can be useful to test different x264/x265 settings.

.. warning:: 
    Resumable encodes do not support shifting zones when encode is resumed. This will create invalid zones. It is recommended to disable resumable encode if you are using zones.

.. code:: python

    from vardautomation import X265, FFV1Encoder

    encoder.video_encoder(X265, settings="path/to/settings/file", resumable=True, qp_file=True)
    encoder.video_lossless_encoder(FFV1Encoder)


Audio
-----
You can set an audio extractor with :py:meth:`~svsfunc.tooling.audio.AudioTooling.audio_extracter` to demux audio from the input file and an audio cutter with :py:meth:`~svsfunc.tooling.audio.AudioTooling.audio_cutter` if you need to trim the audio.
To encode the audio file, you can use the :py:meth:`~svsfunc.tooling.audio.AudioTooling.audio_encoder` method with your favorite audio encoder.

If one or more method is not called, the file produced by the last method (in this order: :py:meth:`~svsfunc.tooling.audio.AudioTooling.audio_encoder` > :py:meth:`~svsfunc.tooling.audio.AudioTooling.audio_cutter` > :py:meth:`~svsfunc.tooling.audio.AudioTooling.audio_extracter`) will be used during muxing.

.. note:: 
    If you are using ``FileInfo2``, you don't need to call :py:meth:`~svsfunc.tooling.audio.AudioTooling.audio_extracter` and :py:meth:`~svsfunc.tooling.audio.AudioTooling.audio_cutter`.

In this example, the source file has 2 audio tracks: the first one is the Japanese dub, 2.0 ch and the second one is the English dub, 5.1 ch.


.. code:: python

    from vardautomation import Eac3toAudioExtracter, EztrimCutter, OpusEncoder

    encoder.set_audio_tracks([1, 2])

    # if file is FileInfo
    encoder.audio_extracter(Eac3toAudioExtracter)
    encoder.audio_cutter(EztrimCutter)

    encoder.audio_encoder(
        OpusEncoder,
        global_settings=dict(bitrate=2 * 96),
        overrides={2: dict(bitrate=6 * 96)}
    )



Chapters
--------
If you are working with Blu-Ray files, you can extract the chapters using vardautomation's ``MplsReader`` or with :py:class:`svsfunc.parse.ParseBD`.
Otherwise, you can use a list of integers where each number represent the first frame of a chapter.

.. code:: python

    from vardautomation import MplsReader

    chapters = MplsReader("path/to/bd/volume").get_playlist()[1].mpls_chapters[0].to_chapters()  # blu ray
    chapters = [0, 1200, 3700, 12500, 32000]  # web

    chapters_names = ["Intro", "OP", "Part A", "Part B", "ED"]

    encoder.make_chapters(chapters, chapters_names)


Muxing
------
You can set the language and title of each audio track. You can also import external audio tracks. If just the path is given, the track will have no title and the language will be undefined.

.. code:: python

    from vardautomation import ENGLISH, JAPANESE, FRENCH, AudioTrack

    encoder.muxer(
        v_title="X265 BD by Encoder@Team",
        a_title=["Opus 2.0", "Opus 5.1"],
        a_lang=[JAPANESE, ENGLISH],
        external_audio=[AudioTrack("my/encoded/audio.opus", "Opus 5.1", FRENCH)]
    )


Running the encode
------------------
You can now run the encoder by calling the :py:meth:`~svsfunc.encode.Encoder.run` method. You can use the :py:meth:`~svsfunc.encode.Encoder.clean_up` method to delete all of the temp files generated during the encode.

.. code:: python

    encoder.run()
    encoder.clean_up()


Utilities
---------
Theses functions can be run whenever you want but make sure they have the required files available:

* :py:meth:`~svsfunc.tooling.utils.UtilsTooling.make_comp` requires source file, the filtered file (will use lossless encode if set) and the final file (``file.name_file_final``).

* :py:meth:`~svsfunc.tooling.utils.UtilsTooling.generate_keyframes` can be run without the final file but it will fallback on the clip passed to the encoder. This may heavily impact performance depending on your filterchain.

.. code:: python

    encoder.make_comp(num_frames=50)
    encoder.generate_keyframes()