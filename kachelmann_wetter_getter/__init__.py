'''Parse weather data on https://kachelmannwetter.com/.
'''

from ._http import *
from ._station_id import *
from ._version import *
from ._weather import *


# only needed to make `help(kachelmann_wetter_getter)` work
__all__ = tuple(_k for _k in locals() if _k[:1] != '_')
