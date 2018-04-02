from os.path import dirname, join

from semver import parse_version_info


__all__ = '__version__', 'version_info',


with open(join(dirname(__file__), 'VERSION'), 'rt') as f:
    __version__ = f.read().strip()

version_info = parse_version_info(__version__)
