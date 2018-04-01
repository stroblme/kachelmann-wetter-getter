from collections.abc import MutableMapping
from logging import getLogger
from threading import Lock
from typing import Optional, Any, Union, ContextManager

from .http import new_session_getter, Session


__all__ = 'LocationCache', 'CouldNotRetrieve', 'NoSuchLocation'


class LocationResult:
    pass


class StationId(int, LocationResult):
    '''An integer that defines the looked up station.
    '''


class CouldNotRetrieve(LocationResult):
    '''An error occured while looking up the station.

    This result is never cached.
    '''
    def __bool__(self):
        return False


class NoSuchLocation(LocationResult):
    '''There is no location with that name.

    This result gets cached unless caching of lookup failures is deactivated.
    '''
    def __bool__(self):
        return False


could_not_retrieve = CouldNotRetrieve()
no_such_location = NoSuchLocation()

AnyLocation = Union[LocationResult, str, int]

logger = getLogger(__name__)


class LocationCache:
    '''Look up queryable locations by name.
    '''
    SEARCH_URL = 'https://kachelmannwetter.com/de/wetter/search'

    def __init__(self, *,
                 lock         : Optional[ContextManager[Any]]     = None,
                 cache        : Optional[MutableMapping]          = None,
                 get_session  : Optional[ContextManager[Session]] = None,
                 cache_absent : Optional[bool]                    = None):
        '''Retrieve a location for a user input.

        Parameters
        ----------
        cache_absent
            Cache misses, too.
        '''
        if lock is None:
            lock = Lock()
        if cache is None:
            cache = {}
        if get_session is None:
            get_session = new_session_getter(self.__class__.__name__)
        if cache_absent is None:
            cache_absent = True

        self.lock = lock
        self.cache = cache
        self.get_session = get_session
        self.cache_absent = cache_absent

    def search_location(self, name:str) -> LocationResult:
        '''Search for a location by name.

        Parameters
        ----------
        name : str
            name of the location

        Returns
        -------
        StationId
            Result of the search.
        CouldNotRetrieve
            Nothing at all was found.
        NoSuchLocation
            There was an error requesting the result.
        '''
        data={
            'forecast_action': 'wetter',
            'forecast_input': name,
        }
        with self.get_session() as session:
            try:
                with session.post(self.SEARCH_URL,
                                  allow_redirects=False,
                                  data=data) as resp:
                    status_code = resp.status_code
                    location = resp.headers.get('Location')
            except Exception:
                logger.error('Could not query', exc_info=True)
                return could_not_retrieve

        if status_code not in range(300, 400):
            if status_code in range(200, 300):
                return no_such_location
            else:
                return could_not_retrieve

        *_, stationid_name = location.rsplit('/', 1)
        stationid, *_ = stationid_name.split('-', 1)
        stationid = int(stationid)

        return StationId(stationid)

    def get_location(self, name:str) -> Optional[StationId]:
        '''Search for a location by name and cache the result

        Parameters
        ----------
        name : str
            an optional name that is used for debugging purposes

        Returns
        -------
        StationId
            Result of the search.
        None
            Nothing at all was found or there was an error.
        '''
        with self.lock:
            result = self.cache.get(name)
            if result is not None:
                return result

            result = self.search_location(name)
            if isinstance(result, CouldNotRetrieve):
                return 

            if not isinstance(result, NoSuchLocation):
                self.cache[name] = result
            else:
                if self.cache_absent:
                    self.cache[name] = result
                result = None
            
            return result

    def get_station_id(self, location:AnyLocation, **kw) -> Optional[int]:
        '''
        Look up a station ID or extract the result.

        Parameters
        ----------
        location
            Either the [name | number] of a location, or the result of
            [get_location() | search_location()].
        kw
            Any keyword arguments are passed to get_location().

        Returns
        -------
        int
            Number it the station.
        None
            Nothing at all was found or there was an error.
        '''
        if isinstance(location, str):
            try:
                return int(location)
            except ValueError:
                pass

            location = self.search_location(location, **kw)

        if isinstance(location, int):
            return +location
        elif not isinstance(location, LocationResult):
            raise TypeError(f'type(location)={type(location)!r} is not a Location')
