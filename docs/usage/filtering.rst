Using svsfunc.filtering
=======================

The :py:class:`svsfunc.filtering.BaseFiltering` class is an abstract base class that provide a set of methods useful to create filterchains.

To create your filterchain, you need to create a class that inherits from :py:class:`svsfunc.filtering.BaseFiltering`. You also need to provide a :py:meth:`~svsfunc.filtering.BaseFiltering.filter` method that takes no argument and returns a ``vs.VideoNode``.

You can add clips to a preview list using the :py:meth:`~svsfunc.filtering.BaseFiltering.add_preview` method. To output the preview clips, use the :py:meth:`~svsfunc.filtering.BaseFiltering.set_outputs` methods.
You can also get a clip from the list of preview clips with the :py:meth:`~svsfunc.filtering.BaseFiltering.get_clip` method.

.. code:: python

    from svsfunc import EpisodeInfo, BaseFiltering
    from vstools import initilize_clip, fininalize_clip, vs

    class MyFilterchain(BaseFiltering):
        def __init__(self, source: EpisodeInfo[vs.VideoNode]):
            self.source = source
        
        def filter(self) -> vs.VideoNode:
            src = initilize_clip(self.source.clip)
            self.add_preview(src, "source")
            
            denoise = ...
            self.add_preview(denoise, "denoise")

            if self.source.op_ranges:
                op_fix = ep_specific_function(denoise)
                self.add_preview(op_fix, "fix op")
      
            grain = ...
            self.add_preview(grain, "grain")

            return fininalize_clip(grain)

        def ep_specific_function(self, clip: vs.VideoNode) -> vs.VideoNode:
            raise NotImplementedError

You can also create methods that will be overridden for some/each episode.

.. code:: python

    class Episode1Filterchain(MyFilterchain):
        def ep_specific_function(self, clip: vs.VideoNode) -> vs.VideoNode:
            ...
    
    class Episode2Filterchain(MyFilterchain):
        def ep_specific_function(self, clip: vs.VideoNode) -> vs.VideoNode:
            ...

Example usage of the filterchain:

.. code:: python
    
    filterchain = Episode1Filterchain(source)

    if __name__ == "__main__":
        enc = Encoder(source.file, filterchain.filter())
        ...

    elif __name__ == "__vapoursynth__":
        filterchain.filter().set_output()

    elif __name__ == "__vspreview":
        from lvsfunc import stack_planes

        filterchain.filter()
        filterchain.set_outputs(preview_func=stack_planes)

