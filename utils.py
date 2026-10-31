import asyncio
import logging
import os
import random
from datetime import datetime

import aiohttp

logger = logging.getLogger(__name__)

WEATHER_URL = 'https://api.openweathermap.org/data/2.5/weather'
CAT_URL = 'https://api.thecatapi.com/v1/images/search'
RATES_URL = 'https://open.er-api.com/v6/latest'
AVATAR_URL = 'https://robohash.org'
AVATAR_SETS = ('set1', 'set4')
CURRENCIES = ('USD', 'EUR', 'CNY')
MOSCOW = (55.75222, 37.61556)

BREEDS = {
    'Абиссинская': 'abys',
    'Бенгальская': 'beng',
    'Сиамская': 'siam',
    'Сибирская': 'sibe',
    'Рэгдолл': 'ragd',
    'Мейн-кун': 'mcoo',
    'Персидская': 'pers',
    'Британская': 'bsho',
}


class ApiError(Exception):
    pass


async def fetch_json(url, params=None):
    timeout = aiohttp.ClientTimeout(total=10)
    logger.debug('GET %s', url)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    logger.warning('Сервис %s ответил кодом %s', url, resp.status)
                    raise ApiError(f'Сервис ответил кодом {resp.status}')
                data = await resp.json(content_type=None)
                logger.debug('Ответ от %s получен', url)
                return data
    except aiohttp.ClientError as e:
        logger.warning('Сетевая ошибка при запросе %s: %s', url, type(e).__name__)
        raise ApiError(f'Сетевая ошибка ({type(e).__name__})')
    except asyncio.TimeoutError:
        logger.warning('Таймаут при запросе %s', url)
        raise ApiError('Сервис не ответил вовремя')
    except ValueError:
        logger.warning('Некорректный JSON в ответе %s', url)
        raise ApiError('Некорректный ответ сервиса')


def get_user_info(update):
    user = update.effective_user
    message = update.effective_message
    first_name = user.first_name or ''
    last_name = user.last_name or ''
    date = message.date if message and message.date else datetime.now()
    return {
        'chat_id': update.effective_chat.id,
        'user_id': user.id,
        'username': user.username,
        'first_name': first_name,
        'full_name': f'{first_name} {last_name}'.strip(),
        'language': user.language_code,
        'chat_type': update.effective_chat.type,
        'timestamp': int(date.timestamp()),
    }


def build_avatar_url(info):
    seed = f"{info['username'] or info['user_id']}-{info['timestamp']}-{random.randint(1, 9999)}"
    avatar_set = random.choice(AVATAR_SETS)
    return f'{AVATAR_URL}/{seed}?set={avatar_set}&size=400x400'


async def get_cat(breed_id=None, breed_name=None):
    params = {'limit': 1, 'has_breeds': 1}
    if breed_id:
        params['breed_ids'] = breed_id
    data = await fetch_json(CAT_URL, params)
    try:
        item = data[0]
        url = item['url']
    except (KeyError, IndexError, TypeError):
        logger.warning('Пустой или неожиданный ответ TheCatAPI (breed_id=%s)', breed_id)
        raise ApiError('Для этой породы фото не найдено')
    breeds = item.get('breeds') or []
    if breeds and breeds[0].get('name'):
        breed = breeds[0]['name']
    elif breed_name:
        breed = breed_name
    else:
        breed = 'неизвестная порода'
    logger.info('Получено фото котика, порода: %s', breed)
    return url, breed


def wind_advice(speed):
    if speed < 5:
        return '☀️ Погода хорошая, ветра почти нет'
    if speed < 10:
        return '🌬️ На улице ветрено, оденьтесь чуть теплее'
    if speed < 20:
        return '💨 Ветер очень сильный, будьте осторожны, выходя из дома'
    return '🌪️ На улице шторм, на улицу лучше не выходить'


async def get_weather(lat, lon):
    key = os.getenv('TOKEN_WEATHER')
    if not key:
        logger.error('Не задан ключ TOKEN_WEATHER в .env')
        raise ApiError('Не задан ключ TOKEN_WEATHER в файле .env')
    params = {'APPID': key, 'lang': 'ru', 'units': 'metric', 'lat': lat, 'lon': lon}
    data = await fetch_json(WEATHER_URL, params)
    try:
        city = data.get('name') or 'Неизвестное место'
        weather = data['weather'][0]['description']
        temp = data['main']['temp']
        feels_like = data['main']['feels_like']
        wind_speed = data['wind']['speed']
    except (KeyError, IndexError, TypeError):
        logger.warning('Неожиданная структура ответа OpenWeather')
        raise ApiError('Некорректные данные о погоде')
    logger.info('Погода получена для города %s', city)
    return (
        f'Сейчас в {city}: {weather}\n'
        f'🌡️ Температура: {temp}°C (ощущается как {feels_like}°C)\n'
        f'💨 Ветер: {wind_speed} м/с\n'
        f'{wind_advice(wind_speed)}'
    )


async def get_rates():
    lines = []
    for base in CURRENCIES:
        data = await fetch_json(f'{RATES_URL}/{base}')
        try:
            if data['result'] != 'success':
                logger.warning('Сервис курсов вернул result=%s для %s', data['result'], base)
                raise ApiError('Сервис курсов вернул ошибку')
            rub = data['rates']['RUB']
        except (KeyError, TypeError):
            logger.warning('Неожиданная структура ответа ExchangeRate-API для %s', base)
            raise ApiError('Некорректные данные о курсах')
        lines.append(f'1 {base} = {rub:.2f} ₽')
    logger.info('Курсы валют получены')
    return '💱 Курс к рублю:\n' + '\n'.join(lines)