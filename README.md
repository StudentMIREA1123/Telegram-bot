# Telegram-бот Praktika_MIREAbot

Учебный Telegram-бот на Python (python-telegram-bot v22+, aiohttp). Бот: https://t.me/Praktika_MIREAbot

## Возможности

| Кнопка / команда | Что делает | Внешний API |
|---|---|---|
| `/start` | приветствие и главное меню | Telegram Bot API |
| `/myid`, «Мой ID» | ID, имя, username, язык, тип чата | Telegram Bot API |
| «Фото котика» | фото котика выбранной породы (меню из 8 пород или случайная) с подписью | [TheCatAPI](https://thecatapi.com/) |
| «Сгенери аватар» | уникальный робот или котик по строке из username, времени и случайного числа | [Robohash](https://robohash.org/) |
| «Курс валют» | курс USD, EUR и CNY к рублю | [ExchangeRate-API](https://www.exchangerate-api.com/docs/free) |
| «Погода сегодня» | погода по геолокации и совет на основе показателя скорости ветра (геолокация доступна только в мобильной версии Telegram) | [OpenWeather](https://openweathermap.org/api) |

## Структура проекта

```
telegram-bot-praktika/
├── main.py             # точка входа
├── bot.py              # run_bot(): сборка приложения, регистрация обработчиков
├── handlers.py         # обработчики сообщений, команд и кнопок
├── utils.py            # запросы к внешним API и вспомогательные функции
├── logger_config.py    # настройка логирования
└──  requirements.txt   # зависимости
```

## Быстрый старт

```bash
git clone https://github.com/StudentMIREA1123/Telegram-bot.git
cd Telegram-bot
python -m venv venv
source venv/bin/activate          # Windows PowerShell: venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Создайте в корне проекта папку .env и вставте свои TOKEN= и TOKEN_WEATHER=

python main.py
```

## Настройка (.env)

```
TOKEN=токен_бота_от_BotFather
TOKEN_WEATHER=ключ_OpenWeather
LOG_LEVEL=INFO
```

Файл `.env` в репозиторий не попадает. Команды для меню бота задаются в BotFather (`/mybots` → Edit Bot → Edit Commands):

```
start - Запустить бота
myid - Узнать свой ID
```

## Обработка ошибок

- Все сетевые запросы идут через `fetch_json`: таймаут 10 секунд, перехват ошибок сети, таймаутов, неверного JSON и статуса не 200 с преобразованием в собственное исключение `ApiError`.
- Разбор ответов API защищён от `KeyError`, `IndexError`, `TypeError`.
- Ошибки отправки фото перехватываются как `TelegramError`.
- Нет геолокации: подставляется Москва. Нет токена: понятное сообщение при запуске.
- Необработанные исключения ловит общий `error_handler`.

## Логирование

Логи пишутся в консоль и в `logs/bot.log`. Формат: `время | уровень | модуль | сообщение`. Уровень задаётся переменной `LOG_LEVEL`. В логи не попадают токены, текст сообщений и координаты.

