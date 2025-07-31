from .bdmv import *  # noqa: F401, F403
from .filterchain import *  # noqa: F401, F403
from .episode_info import *  # noqa: F401, F403
from .parse import *  # noqa: F401, F403
from .utils import *  # noqa: F401, F403

try:
    # only import Encoder class if vardautomation is installed on the system
    # will be completly removed later
    import vardautomation  # noqa: F401
    from .encode import *  # noqa: F401, F403

    import warnings
    warnings.warn("Vardautomation is deprecated, please use to vs-muxtools instead.", category=DeprecationWarning)

except ImportError:
    ...
