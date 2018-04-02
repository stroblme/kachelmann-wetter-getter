from collections import namedtuple
from os.path import dirname, join
from re import match


__all__ = '__version__', 'version_info',


Version = namedtuple('Version', 'major minor maintenance tag metadata')

with open(join(dirname(__file__), 'VERSION'), 'rt') as f:
    __version__ = f.read().strip()

groups = match('\A(\d+)\.(\d+)\.(\d+)([a-z]+\d+)?(?:\.([a-z]+\d+))?\Z', __version__).groups()

version_info = Version(*(int(s) for s in groups[:3]), *groups[3:])
