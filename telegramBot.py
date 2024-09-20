import json
import os
import telebot
import requests
from dotenv import load_dotenv
from telebot import types
from requests.exceptions import ReadTimeout
from bs4 import BeautifulSoup as bs

load_dotenv()

API_TG = os.getenv('API_TELEGRAM')
API_FORECAST = os.getenv('API_FOR')

if not API_TG or not API_FORECAST:
    raise ValueError("API keys are missing. Please check your .env file.")

bot = telebot.TeleBot(API_TG)

waiting_for_weather_command = {}
waiting_for_currency_input = {}


def send_long_message(chat_id, text):
    """Send a long message to Telegram chat, split into parts if necessary."""
    max_length = 4096
    for i in range(0, len(text), max_length):
        bot.send_message(chat_id, text[i:i + max_length], parse_mode='HTML')


def get_weather_emoji(description):
    """Return an emoji based on the weather description."""
    description = description.lower()
    if 'clear' in description:
        return '☀️'
    elif 'cloud' in description:
        return '☁️'
    elif 'rain' in description or 'drizzle' in description:
        return '🌧️'
    elif 'thunderstorm' in description:
        return '⛈️'
    elif 'snow' in description:
        return '❄️'
    elif 'mist' in description or 'fog' in description:
        return '🌫️'
    else:
        return '🌤️'


@bot.message_handler(commands=['start', 'run'])
def start(message):
    bot.send_message(message.chat.id, f'Hello, {message.from_user.first_name}!')
    bot.send_message(message.chat.id, 'Use /help to see available commands.')


@bot.message_handler(commands=['site', 'web', 'website'])
def site(message):
    bot.send_message(message.chat.id, 'Opening website: ')


@bot.message_handler(commands=['music'])
def music(message):
    text = (
        "🎵 *Music Resources* 🎵\n\n"
        "[Archive.org](https://archive.org)\n"
        "[FlacWorld.ru](https://flacworld.ru)\n"
        "[Lossless-flac.com](https://lossless-flac.com)"
    )
    bot.send_message(message.chat.id, text, parse_mode='Markdown')


@bot.message_handler(commands=['info'])
def info(message):
    bot.send_message(message.chat.id, 'This bot is created by @morry_dev.')


@bot.message_handler(commands=['currency_uah'])
def currency(message):
    try:
        # Fetch exchange rates from PrivatBank API
        response = requests.get("https://api.privatbank.ua/p24api/pubinfo?exchange&json&coursid=11")
        data = response.json()

        # Extract relevant currencies
        relevant_currencies = ['USD', 'EUR', 'RUR', 'BTC']

        header = f"<pre>\n{'Currency' :^10} | {'Buy' :^7} | {'Sell' :^7}\n</pre>" + "-" * 30

        exchange_info = "\n".join(
                    [
                        f"{item['ccy']:^11}| {float(item['buy']):^7.2f} | {float(item['sale']):^8.2f}"
                        for item in data if item['ccy'] in relevant_currencies
                    ])

        if not exchange_info:
            exchange_info = "No exchange rates available for the specified currencies."

        response_text = f"<pre>Exchange Rates => UAH (PrivatBank)\n{header}\n{exchange_info}\n\n</pre>"
        bot.send_message(message.chat.id, response_text, parse_mode='HTML')
    except Exception as e:
        bot.send_message(message.chat.id, f"Error fetching exchange rates: {e}")


@bot.message_handler(commands=['currency', 'USD', 'USD', 'GBP', 'RUR', 'EUR'])
def currency(message):
    chat_id = message.chat.id

    # Create a custom keyboard
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton('USD'),
        types.KeyboardButton('RUB'),
        types.KeyboardButton('GBP'),
        types.KeyboardButton('CNY'),
        types.KeyboardButton('EUR')
    )

    # Prompt user to select a currency
    bot.send_message(
        chat_id,
        'Please select the currency code to get the exchange rates:',
        reply_markup=markup
    )

    waiting_for_currency_input[chat_id] = True


def process_currency_input(message):
    chat_id = message.chat.id
    currency_code = message.text.strip().upper()  # Get user input and convert to uppercase
    if currency_code not in ['USD', 'EUR', 'RUB', 'CNY', 'GBP']:
        bot.send_message(chat_id, 'Invalid currency code. Please enter one of the following: USD, EUR, RUB, CNY, GBP.')
        return

    try:
        price_datetime, exchange_rates = get_exchange_list_xrates(currency_code)
        # Map full currency names to their codes
        currency_map = {
            'US Dollar': 'USD',
            'Euro': 'EUR',
            'Russian Ruble': 'RUB ',
            'Chinese Yuan Renminbi': 'CNY',
            'British Pound': 'GBP'
        }

        relevant_currencies = currency_map.keys()

        header = f"<pre>\n{'Currency' :^10} | {'Buy' :^11}\n</pre>" + "-" * 25

        exchange_info = "\n".join(
                    [
                        f"{currency_code:^10} > {rate:>7.2f} {currency_map[currency]}"
                        for currency, rate in exchange_rates.items()
                        if currency in relevant_currencies
                    ])

        if not exchange_info:
            exchange_info = "No exchange rates available for the specified currencies."

        response = (f"<pre>Exchange Rates => {currency_code}\n{header}\n{exchange_info}</pre>\n<b>Last "
                    f"updated:</b> {price_datetime}")
        bot.send_message(message.chat.id, response, parse_mode='HTML')
    except Exception as e:
        bot.send_message(message.chat.id, f"Error fetching exchange rates: {e}")

    bot.send_message(chat_id, '', reply_markup=types.ReplyKeyboardRemove())


def get_exchange_list_xrates(currency, amount=1):
    # делаем запрос на x-rates.com, чтобы получить актуальные курсы обмена распространенных валют
    content = requests.get(f"https://www.x-rates.com/table/?from={currency}&amount={amount}").content
    # инициализируем beautifulsoup
    soup = bs(content, "html.parser")
    # получить последнее обновленное время
    price_datetime = soup.find_all("span", attrs={"class": "ratesTimestamp"})[0].text
    # получить таблицы курсов валют
    exchange_tables = soup.find_all("table")
    exchange_rates = {}
    for exchange_table in exchange_tables:
        for tr in exchange_table.find_all("tr"):
            # for each row in the table
            tds = tr.find_all("td")
            if tds:
                currency = tds[0].text.strip()
                # получаем курс обмена
                try:
                    exchange_rate = float(tds[1].text.strip())
                    exchange_rates[currency] = exchange_rate
                except ValueError:
                    pass  # Ignore any rows that don't contain valid numbers
    return price_datetime, exchange_rates


@bot.message_handler(commands=['show_id'])
def show_id(message):
    user_id = message.from_user.id
    bot.send_message(message.chat.id, f'<b>Your ID:</b> <code>{user_id}</code>', parse_mode='html')


@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
<b>Bot Commands:</b>
<b>/start</b> - Starts the bot and sends a welcome message.
<b>/help</b> - Sends a list of available commands and their descriptions.
<b>/info</b> - Sends information about the bot.

<b>Currency Commands:</b>
<b>/currency</b> - Shows the latest exchange rates for major currencies (e.g., USD, EUR, GBP).
<b>/currency_uah</b> - Shows the latest exchange rates with respect to the Ukrainian Hryvnia (UAH).
    
<b>Weather Commands:</b>
<b>/weather_tralee</b> - Shows the current weather in Tralee.
<b>/weather</b> - Provides the current weather in your specified city.
    
<b>Another Commands:</b>
<b>/show_id</b> - Displays your Telegram user ID.
<b>/website</b> - Provides a link to your personal website. (not worked yet)
<b>/music</b> - Shares a collection of FLAC music files for download.
    """
    bot.send_message(message.chat.id, help_text, parse_mode='html')


@bot.message_handler(content_types=['photo', 'audio', 'document', 'video', 'sticker', 'voice'])
def handle_media(message):
    bot.send_message(message.chat.id, "Sorry, this type of message is not currently processed by the bot.\n/start")


def fetch_weather(city_name):
    try:
        res = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={API_FORECAST}'
                           f'&units=metric', timeout=10)
        if res.status_code == 200:
            data = json.loads(res.text)
            main_weather = data.get('main', {})
            weather = data.get('weather', [{}])[0]
            wind = data.get('wind', {})

            # Extracting data
            temperature = main_weather.get('temp', 'N/A')
            wind_speed = wind.get('speed', 'N/A')
            wind_mps = round(wind_speed * 5 / 18, 2)
            weather_description = weather.get('description', 'No description available')

            # Get emoji for weather conditions
            weather_emoji = get_weather_emoji(weather_description)

            # Format response with emoji
            response = (f'<b>🌤️ Current Weather in {city_name.capitalize()}:</b>\n\n'
                        f'<b>Temperature:</b> {temperature}°C 🌡️\n'
                        f'<b>Weather cond.:</b> {weather_description.capitalize()} {weather_emoji}\n'
                        f'<b>Wind speed:</b> {wind_mps} m/sec 💨')

            return response
        else:
            return f'Error: {res.status_code}'
    except ReadTimeout:
        return 'The request timed out. Please try again later.'
    except Exception as e:
        return f'Error fetching weather: {e}'


@bot.message_handler(commands=['weather'])
def get_weather(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Please enter the name of the city to get the weather information.')
    waiting_for_weather_command[chat_id] = True


@bot.message_handler(commands=['weather_tralee'])
def weather_tralee(message):
    city_name = 'Tralee'
    response = fetch_weather(city_name)
    bot.reply_to(message, response, parse_mode='HTML')


@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id

    if waiting_for_currency_input.get(chat_id):
        process_currency_input(message)
        waiting_for_currency_input[chat_id] = False
    elif waiting_for_weather_command.get(chat_id):
        city_name = message.text.strip().lower()
        response = fetch_weather(city_name)
        bot.reply_to(message, response, parse_mode='HTML')
        waiting_for_weather_command[chat_id] = False
    else:
        if message.text.lower() == "иди нахуй":
            bot.send_message(chat_id, 'Слыш, самый умный что-ли?? Сходи-ка ты сам туда')
        else:
            bot.send_message(chat_id, '/start')


def main():
    while True:
        try:
            bot.polling(none_stop=True, timeout=30, long_polling_timeout=30)
        except ReadTimeout:
            print("ReadTimeout occurred. Retrying...")
        except Exception as e:
            print(f"An error occurred: {e}")


if __name__ == '__main__':
    main()
