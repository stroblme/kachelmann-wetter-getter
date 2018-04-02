'''Parse weather data on https://kachelmannwetter.com/.
'''

import os as _os

from .http import *
from .station_id import *
from .weather import *


with open(_os.path.join(_os.path.dirname(__file__), 'VERSION'), 'rt') as _f:
    __version__ = tuple(int(s) for s in _f.read().strip().split('.'))

# only needed to make `help(kachelmann_wetter_getter)` work
__all__ = tuple(_k for _k in locals() if _k[:1] != '_')
