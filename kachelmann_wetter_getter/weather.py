from collections import namedtuple
from logging import getLogger
from typing import Optional, Sequence, NewType

from dataclasses import dataclass
from lxml.html.html5parser import fragment_fromstring

from .http import new_session_getter, SessionGetter
from .station_id import AnyLocation, LocationCache


__all__ = 'KachelmannWetter',

logger = getLogger(__name__)


Kph = NewType('Kph', float)
DegCelsius = NewType('DegCelsius', float)
Percent = NewType('Percent', float)
Millimeters = NewType('Millimeters', float)


@dataclass
class SkyData:
    friendly_name: str  # "bedeckt"
    symbol: str         # "overcast"

@dataclass
class WindData:
    direction: str   # "sw"
    strength: Kph    # 16.0

@dataclass
class NextHoursData:
    hours: int               # 13
    minutes: int             # 0
    sky: SkyData
    temperature: DegCelsius  # 3.0
    chance_of_rain: Percent  # 0.88

@dataclass
class NextDaysData:
    friendly_name: str       # "Montag"
    date: str                # "2.April"
    temp_min: DegCelsius
    temp_max: DegCelsius
    avg_wind: WindData
    max_wind: Kph
    amount_rain: Millimeters
    risks: Sequence[SkyData]
    morning: SkyData
    afternoon: SkyData
    evening: SkyData

@dataclass
class NextHoursDaysData:
    hours: Sequence[NextHoursData]
    days: Sequence[NextDaysData]


namespaces = {
    'xhtml':'http://www.w3.org/1999/xhtml',
}


def has_class(name):
    return f'contains(concat(" ", @class, " "), " {name} ")'


def text_content(node):
    if node is None:
        return node
    elif isinstance(node, str):
        pass
    elif isinstance(node, bytes):
        node = node.decode('UTF-8', 'replace')
    else:
        text_func = getattr(node, 'text_content', None)
        if text_func is not None:
            node = text_func()
        else:
            node = node.text

    return node.replace('\xA0', ' ').strip()


def extract_symbol(img):
    return img.get('src').rsplit('/', 1)[-1].split('.')[0].split('_', 2)[1]


def xpath(node, path):
    if node is None:
        return ()
    else:
        return node.xpath(path, namespaces=namespaces)


def parse_hour(hour_data):
    hours, = xpath(hour_data, f'./xhtml:div[{has_class("fc-hours")}]/text()')
    symbol, = xpath(hour_data, f'./xhtml:div[{has_class("fc-symbol")}]')
    img, = xpath(symbol, './xhtml:img')
    temperature, = xpath(hour_data, f'./xhtml:div[{has_class("fc-temp")}]/text()')
    chance_of_rain, = xpath(hour_data, f'./xhtml:div[{has_class("fc-rain")}]/text()')

    hours, minutes = (
        int(s, 10) for s in text_content(hours).split(maxsplit=1)[0].split(':', 1)
    )
    friendly_name = symbol.get('title')
    symbol = extract_symbol(img)
    temperature = float(text_content(temperature).split('°', 1)[0])
    chance_of_rain = float(text_content(chance_of_rain).split('%', 1)[0]) / 100.0

    return NextHoursData(
        hours=hours,
        minutes=minutes,
        sky=SkyData(friendly_name=friendly_name, symbol=symbol),
        temperature=temperature,
        chance_of_rain=chance_of_rain,
    )


def parse_day(day_data):
    friendly_name, date = xpath(day_data, f'./xhtml:div[{has_class("panel-heading")}]/text()')
    body, = xpath(day_data, f'./xhtml:div[{has_class("panel-body")}]')
    morning, = xpath(body, f'./xhtml:div[{has_class("wsymbol-morning")}]/xhtml:img')
    afternoon, = xpath(body, f'./xhtml:div[{has_class("wsymbol-afternoon")}]/xhtml:img')
    evening, = xpath(body, f'./xhtml:div[{has_class("wsymbol-evening")}]/xhtml:img')
    minmax, = xpath(body, f'./xhtml:div[{has_class("day-temp-maxmin")}]')
    temp_max, = xpath(
        minmax,
        f'./xhtml:div[{has_class("day-temp-max")}]/xhtml:div[{has_class("day-fc-temp")}]/text()',
    )
    temp_min, = xpath(
        minmax,
        f'./xhtml:div[{has_class("day-temp-min")}]/xhtml:div[{has_class("day-fc-temp")}]/text()',
    )
    risks, windrain = xpath(body, f'./xhtml:div[{has_class("day-risks")}]/xhtml:div')

    friendly_name = text_content(friendly_name)
    date = text_content(date)
    temp_min = float(text_content(temp_min).split('°', 1)[0])
    temp_max = float(text_content(temp_max).split('°', 1)[0])
    avg_wind = '''TODO'''
    max_wind = '''TODO'''
    amount_rain = '''TODO'''
    risks = '''TODO'''
    morning = SkyData(friendly_name=morning.get('alt'), symbol=extract_symbol(morning))
    afternoon = SkyData(friendly_name=afternoon.get('alt'), symbol=extract_symbol(afternoon))
    evening = SkyData(friendly_name=evening.get('alt'), symbol=extract_symbol(evening))

    return NextDaysData(
        friendly_name=friendly_name,
        date=date,
        temp_min=temp_min,
        temp_max=temp_max,
        avg_wind=avg_wind,
        max_wind=max_wind,
        amount_rain=amount_rain,
        risks=risks,
        morning=morning,
        afternoon=afternoon,
        evening=evening,
    )

class KachelmannWetter:
    AJAX_URL = 'https://kachelmannwetter.com/de/ajax_pub'

    def __init__(self, *,
                 get_session    : Optional[SessionGetter] = None,
                 location_cache : Optional[LocationCache] = None):
        if get_session is None:
            get_session = new_session_getter(self.__class__.__name__)
        if location_cache is None:
            location_cache = LocationCache()

        self.get_session = get_session
        self.location_cache = location_cache

    def next_hours_days(self, location:AnyLocation) -> Optional[NextHoursDaysData]:
        city_id = self.location_cache.get_station_id(location)
        if city_id is None:
            return

        url = f'{self.AJAX_URL}/weathernexthoursdays?city_id={city_id}&lang=de&units=de&tf=1'
        with self.get_session() as session:
            with session.get(url) as resp:
                status_code = resp.status_code
                if not resp.status_code in range(200, 300):
                    logger.warn('Could not retrieve date for url=%r, status_code=%r',
                                url, status_code)
                    return

                content = resp.text

        root = fragment_fromstring(content, create_parent='root')

        data_hours = xpath(
            root,
            f'/root/xhtml:div[{has_class("nexthours-scroll")}]/xhtml:div/xhtml:div',
        )
        data_hours = tuple(parse_hour(hour_data) for hour_data in data_hours)

        data_days = xpath(root, f'/root/xhtml:div[{has_class("day-row")}]/xhtml:div/xhtml:div')
        data_days = tuple(parse_day(day_data) for day_data in data_days)

        return NextHoursDaysData(data_hours, data_days)
