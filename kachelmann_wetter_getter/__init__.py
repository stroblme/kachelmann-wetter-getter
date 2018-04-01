'''Parse weather data on https://kachelmannwetter.com/.
'''

import os as _os
import sys as _sys


if _sys.version_info < (3, 6):
    actual_version, *_ = _sys.version.split(maxsplit=1)
    raise ImportError(f'At least Python 3.6 is needed, found={actual_version}')

with open(_os.path.join(_os.path.dirname(__file__), 'VERSION'), 'rt') as _f:
    __version__ = tuple(int(s) for s in _f.read().strip().split('.'))


from .http import *
from .station_id import *
from .weather import *


__all__ = tuple(_k for _k in locals() if _k[:1] != '_')
