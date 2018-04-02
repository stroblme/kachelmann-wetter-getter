from contextlib import contextmanager
from logging import getLogger
from threading import Lock
from typing import Callable, Optional, ContextManager

from requests import Session
from semver import format_version

from ._version import version_info


__all__ = 'set_user_agent',


default_user_agent = (f'Kachelmann-Wetter-Getter/'
                      f'v{version_info[0]}.{version_info[1]}.{version_info[2]}')

headers = {
    'User-Agent': default_user_agent,
}

header_modication_tracker = object()

logger = getLogger(__name__)

SessionGetter = Callable[[], ContextManager[Session]]


def invalidate_sessions():
    '''Invalidates all sessions created with new_session_getter().
    '''
    global header_modication_tracker
    header_modication_tracker = object()


def set_user_agent(user_agent: str, *, replace: bool = False):
    '''Defines the User-Agent header to send to remote hosts.

    Parameters
    ----------
    user_agent : str
        new user agent string to use
    replace : bool
        append the default user agent unless true
    '''
    if replace:
        headers['User-Agent'] = user_agent
    else:
        headers['User-Agent'] = f'{user_agent} {default_user_agent}'

    invalidate_sessions()


def new_session() -> Session:
    '''Create a new web session.

    Returns
    -------
    Session
        a new requests session
    '''
    session = Session()
    session.headers.update(headers)
    return session


def new_session_getter(name: Optional[str] = None) -> SessionGetter:
    '''Create a session cache that returns an existing session unless the user agent was modified.

    Parameters
    ----------
    name : str
        an optional name that is used for debugging purposes

    Returns
    -------
    Session
        a new requests session
    '''
    lock = Lock()

    if name is None:
        name = '<unspecified>'

    def getter():
        @contextmanager
        def lock_session_context():
            with lock:
                yield session

        while True:
            logger.debug('Creating a new session for name=%r', name)
            with new_session() as session:
                old_tracker = header_modication_tracker
                while True:
                    cur_tracker = header_modication_tracker
                    if cur_tracker is not old_tracker:
                        old_tracker = cur_tracker
                        break

                    yield lock_session_context()

    return getter().__next__
