#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import logging
import json
import random
from timeit import default_timer as timer
import requests
import datetime
from imdb import IMDb
from setup import PROXY, TOKEN, YANDEX_API, RAPID_API
from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, Filters, MessageHandler, Updater, CallbackQueryHandler
from classes import Logs, CSVStats, parseDateFromString

date = datetime.date.today().strftime("%m-%d-%Y")
bot = Bot(
    token=TOKEN,
    base_url=PROXY,  # delete it if connection via VPN
)
# Enable logging
joke_id = ""
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.

def average_time(function):
    def inner(update: Update, context: CallbackContext):
        t = timer()
        res = function(update, context)
        t = (timer() - t)
        update.message.reply_text(f'Время: {t} s!')
        return res

    return inner


def add_log(function):
    def wrapper(*args, **kwargs):
        message = 'button' if args[0].message is None else args[0].message.text
        new_log = {
            "user": args[0].effective_user.username,
            "function": function.__name__,
            "message": message,
            "time": args[0].effective_message.date
        }
        logs = Logs()
        logs.addLog(new_log)
        return function(*args, **kwargs)

    return wrapper


@add_log
def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    text = f"""
Hello, {update.effective_user.first_name}!
Nice to see you here!
If you need help, enter /help command.
"""
    update.message.reply_text(text=text)


@add_log
def chat_help(update: Update, context: CallbackContext):
    """Send a message when the command /help is issued."""
    text = """
    Supported commands:
/start - start bot
/help - show supported commands
/history - show last five logs
/fact_cat - get the most popular fact about cats
/movie - get random movie from top-250 IMDb
/corona_stats - get top-5 COVID-19 infected countries
/corona_stats_dynamics - get dynamic of COVID-19 distribution
/pokemon - get info and image of random pokemon
/joke - bot will make you laugh (probably)
/weather - get current weather info and forecast for the next 12 hours
/fact_year <year> - get interesting fact about particular year (default value - 2020)
/fact_number <number> - get integersting fact about number (default value - random < 1000)
/coin - to flip a coin
"""
    update.message.reply_text(text)


@add_log
def echo(update: Update, context: CallbackContext):
    """Echo the user message."""
    update.message.reply_text(update.message.text)


@add_log
def error(update: Update, context: CallbackContext):
    """Log Errors caused by Updates."""
    logger.warning(f'Update {update} caused error {context.error}')


def history(update: Update, context: CallbackContext):
    """Send a message when the command /logs is issued."""
    logs = Logs()
    logslist = logs.getLastFiveLogs()
    # print(logslist)
    for log in logslist:
        response = ""
        for key, value in log.items():
            response = response + f'{key}: {value}\n'
        update.message.reply_text(response)


def test(update: Update, context: CallbackContext):
    new_log = {
        "user": update.effective_user.first_name,
        "function": "anonym",
        "message": "test",
        "time": update.message.date
    }
    logs = Logs()
    loglist = []
    for _ in range(100000):
        loglist.append(new_log)
    logs.addLogs(loglist)


@add_log
def fact(update: Update, context: CallbackContext):
    maximum = 0
    upvoted_text = ''
    r = requests.get('https://cat-fact.herokuapp.com/facts')
    answer = json.loads(r.text)
    for i in answer['all']:
        if i['upvotes'] > maximum:
            maximum = i['upvotes']
            upvoted_text = i['text']
    update.message.reply_text(upvoted_text)


@add_log
def movie(update: Update, context: CallbackContext):
    ia = IMDb()
    top = ia.get_top250_movies()
    random_movie = top[random.randint(0, 249)]
    id = 'tt' + random_movie.movieID
    info = requests.get(f'http://www.omdbapi.com/?apikey=5a5643&i={id}')
    info = json.loads(info.text)
    # poster = requests.get(f'http://img.omdbapi.com/?apikey=5a5643&i={id}')
    text = f"""
Title: {random_movie.data['title']}
Genre: {info["Genre"]}
Year: {random_movie.data['year']}
Director: {info["Director"]}
Runtime: {info["Runtime"]}
IMDb rating: {random_movie.data['rating']}
Top 250 rank: {random_movie.data['top 250 rank']}
Link: https://www.imdb.com/title/{id}/
"""
    update.message.reply_text(text=text, disable_web_page_preview=False)


@add_log
def pokemon(update: Update, context: CallbackContext):
    num = random.randint(1, 807)
    pokemon_info = requests.get(f'https://pokeapi.co/api/v2/pokemon/{num}/')
    pokemon_info = json.loads(pokemon_info.text)
    text = f"""
Name: {pokemon_info['name'].capitalize()}
Height: {pokemon_info['height']}
Weight: {pokemon_info['weight']}
Type: {pokemon_info['types'][0]['type']['name']}
"""
    bot.send_message(chat_id=update.effective_chat['id'], text=text)
    bot.send_photo(chat_id=update.effective_chat['id'], photo=pokemon_info['sprites']['front_default'])


@add_log
def corona_stats(update: Update, context: CallbackContext):
    if update.message is not None and update.message.from_user == update.effective_user:
        CSVStats.date = parseDateFromString(update.effective_message.text)
    csvStat = CSVStats("todaystats.csv")
    if csvStat.status_code != 200:
        keyboard = [[InlineKeyboardButton("Yes, show me data from previous day", callback_data="True"),
                     InlineKeyboardButton("No, thank you", callback_data="False")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id=update.effective_chat['id'],
                         text=f"Something went wrong. Maybe, there is no data yet from {CSVStats.date}."
                              f"Do you want to now data from previous day?", reply_markup=reply_markup)
    else:
        csvStat.changeRequest()
        top_five = csvStat.getTopFiveProvinces()
        # print(top_five)
        text = "TOP-5 infected regions:\n"
        for i in range(len(top_five)):
            text += f'{i + 1}. {top_five[i]["province"]} - {top_five[i]["new infected"]} infected\n'
        if update.message is not None and update.message.from_user == update.effective_user:
            bot.send_message(chat_id=update.effective_message.chat_id,
                             message_id=update.effective_message.message_id,
                             text=f"COVID-19 statistics dynamics from {CSVStats.date}\n{text}")
        else:
            bot.edit_message_text(chat_id=update.effective_message.chat_id,
                                  message_id=update.effective_message.message_id,
                                  text=f"COVID-19 statistics dynamics from {CSVStats.date}\n{text}")
        CSVStats.date = datetime.date.today().strftime("%m-%d-%Y")


@add_log
def corona_stats_dynamics(update: Update, context: CallbackContext):
    today_stats = CSVStats("today_stats.csv")
    yesterday_stats = CSVStats("yesterday_stats.csv")
    while today_stats.status_code != 200:
        today_stats.date = (datetime.datetime.strptime(today_stats.date, "%m-%d-%Y") -
                            datetime.timedelta(days=1)).strftime("%m-%d-%Y")
        today_stats.changeRequest()
    yesterday_stats.date = (datetime.datetime.strptime(today_stats.date, "%m-%d-%Y") -
                            datetime.timedelta(days=1)).strftime("%m-%d-%Y")
    yesterday_stats.changeRequest()
    today_top_five = today_stats.getTopFiveProvinces()
    yesterday_top_five = yesterday_stats.getTopFiveProvinces()
    text = f"COVID-19 statistics dynamics from {yesterday_stats.date} to {today_stats.date}: \n"
    for i in range(5):
        old_infected = 0
        for j in range(len(yesterday_top_five)):
            if today_top_five[i]["province"] == yesterday_top_five[j]["province"]:
                old_infected = yesterday_top_five[j]["new infected"]
                break
        text += f'{i + 1}. {today_top_five[i]["province"]} - {today_top_five[i]["new infected"]} ' \
                f'(+{today_top_five[i]["new infected"] - old_infected}) infected\n'
    bot.send_message(chat_id=update.effective_message.chat_id, message_id=update.effective_message.message_id,
                     text=f"{text}")


@add_log
def joke(update: Update, context: CallbackContext):
    url = "https://joke3.p.rapidapi.com/v1/joke"
    headers = {
        'x-rapidapi-host': "joke3.p.rapidapi.com",
        'x-rapidapi-key': RAPID_API
    }
    global joke_id
    response = json.loads(requests.request("GET", url, headers=headers).text)
    joke_id = response["id"]
    content = response["content"]
    likes = response["upvotes"]
    dislikes = response["downvotes"]
    keyboard = [[InlineKeyboardButton(f"Like ❤️ {likes}", callback_data="Like"),
                 InlineKeyboardButton(f"Dislike 💔 {dislikes}", callback_data="Dislike"),
                 InlineKeyboardButton("More jokes", callback_data="More jokes")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id=update.effective_chat['id'], text=content, reply_markup=reply_markup)

@add_log
def fact_year(update: Update, context: CallbackContext):
    data = update.message['text'].split()
    year = 0
    try:
        year = data[1]
    except:
        year = 2020
    url = f"https://numbersapi.p.rapidapi.com/{year}/year"
    querystring = {"fragment": "true", "json": "true"}
    headers = {
        'x-rapidapi-host': "numbersapi.p.rapidapi.com",
        'x-rapidapi-key': RAPID_API
    }
    response = requests.request("GET", url, headers=headers, params=querystring)
    response = json.loads(response.text)
    response = f"Year {year}: " + response["text"].capitalize()
    bot.send_message(chat_id=update.effective_chat['id'], text=response)

@add_log
def fact_number(update: Update, context: CallbackContext):
    data = update.message['text'].split()
    number = 0
    try:
        number = data[1]
    except:
        number = random.randint(0, 1000)
    url = f"https://numbersapi.p.rapidapi.com/{number}/math"
    querystring = {"fragment": "true", "json": "true"}
    headers = {
        'x-rapidapi-host': "numbersapi.p.rapidapi.com",
        'x-rapidapi-key': RAPID_API
    }
    response = requests.request("GET", url, headers=headers, params=querystring)
    response = json.loads(response.text)
    response = f"Fact for number {number}: " + response["text"].capitalize()
    bot.send_message(chat_id=update.effective_chat['id'], text=response)

@add_log
def coin(update: Update, context: CallbackContext):
    number = random.randint(0, 1000)
    response = ""
    if number % 2 == 1:
        response = "Heads"
    else:
        response = "Tails"
    bot.send_message(chat_id=update.effective_chat['id'], text=response)

@add_log
def weather(update: Update, context: CallbackContext):
    url = "https://api.weather.yandex.ru/v1/informers/"
    params = {
        'lat': 56.3269,
        'lon': 44.0059,
        'lang': 'ru_RU',
    }
    header = {'X-Yandex-API-Key': YANDEX_API}
    response = requests.get(url, params=params, headers=header).json()

    wind_directions = {
        "nw": "north-western",
        "n": "northern",
        "ne": "north-eastern",
        "e": "eastern",
        "se": "south-eastern",
        "s": "southern",
        "sw": "south-western",
        "w": "western",
        "c": "calm"
    }

    current_temperature = response['fact']['temp']
    feels_like = response['fact']['feels_like']
    condition = response['fact']['condition']
    wind_speed = response['fact']['wind_speed']
    wind_direction = wind_directions[response['fact']['wind_dir']]

    # forecast_date = datetime.strptime(response['forecast']['date'], '%Y-%m-%d').strftime('%d-%m-%Y')
    forecast_date = '-'.join(response['forecast']['date'].split('-')[::-1])

    part_one = response['forecast']['parts'][0]['part_name']
    temp_min_one = response['forecast']['parts'][0]['temp_min']
    temp_max_one = response['forecast']['parts'][0]['temp_max']
    condition_one = response['forecast']['parts'][0]['condition']
    wind_speed_one = response['forecast']['parts'][0]['wind_speed']
    wind_direction_one = wind_directions[response['forecast']['parts'][0]['wind_dir']]

    part_two = response['forecast']['parts'][1]['part_name']
    temp_min_two = response['forecast']['parts'][1]['temp_min']
    temp_max_two = response['forecast']['parts'][1]['temp_max']
    condition_two = response['forecast']['parts'][1]['condition']
    wind_speed_two = response['forecast']['parts'][1]['wind_speed']
    wind_direction_two = wind_directions[response['forecast']['parts'][1]['wind_dir']]

    message = f"""
In Nizhny Novgorod it's now {condition}. The temperature is {current_temperature}°C but feels like {feels_like}°C.
The {wind_direction} wind is at {wind_speed} m/s.

During the {part_one} of {forecast_date} the temperature from {temp_min_one}°C to {temp_max_one}°C is expected,
it's going to be {condition_one}. There's going to be {wind_direction_one} wind at {wind_speed_one} m/s.

In the {condition_two} {part_two} of {forecast_date} you can expect the temperature from {temp_min_two}°C to
{temp_max_two}°C. The winds are going to be {wind_direction_two} at {wind_speed_two} m/s.

Source: Yandex.Weather
More info at {response['info']['url']}
"""
    bot.send_message(chat_id=update.effective_chat['id'], text=message, disable_web_page_preview=True)


def button_corona(update, context):
    query = update.callback_query
    if query['data'] == 'False':
        global bot
        bot.send_message(chat_id=update.callback_query.message.chat['id'], text='Хорошо :)')
    else:
        global date
        CSVStats.date = (datetime.datetime.strptime(CSVStats.date, "%m-%d-%Y") - datetime.timedelta(days=1)).strftime(
            "%m-%d-%Y")
        corona_stats(update, context)


def button_joke(update, context):
    query = update.callback_query
    if query['data'] == 'Like' or query['data'] == "Dislike":
        global joke_id
        url = f"https://joke3.p.rapidapi.com/v1/joke/{joke_id}/upvote" if query['data'] == 'Like' else f"https://joke3.p.rapidapi.com/v1/joke/{joke_id}/downvote" # noqa
        payload = ""
        headers = {
            'x-rapidapi-host': "joke3.p.rapidapi.com",
            'x-rapidapi-key': "837031bcd7msh57190d81a3d0374p19228ejsn5404ac1dd13a",
            'content-type': "application/x-www-form-urlencoded"
        }
        response = requests.request("POST", url, data=payload, headers=headers)
        response = json.loads(response.text)
        content = response["content"]
        likes = response["upvotes"]
        dislikes = response["downvotes"]
        keyboard = [[InlineKeyboardButton(f"Like ❤️ {likes}", callback_data="Like"),
                     InlineKeyboardButton(f"Dislike 💔 {dislikes}", callback_data="Dislike"),
                     InlineKeyboardButton("More jokes", callback_data="More jokes")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "You ❤️ it!" if query['data'] == 'Like' else "You 💔️ it!"
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text=text)
        bot.edit_message_text(message_id=update.callback_query.message.message_id,
                              chat_id=update.callback_query.message.chat.id, text=content, reply_markup=reply_markup)
    elif query['data'] == 'More jokes':
        joke(update, context)


def main():
    updater = Updater(bot=bot, use_context=True)

    # on different commands - answer in Telegram
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('help', chat_help))
    updater.dispatcher.add_handler(CommandHandler('history', history))
    updater.dispatcher.add_handler(CommandHandler('test', test))
    updater.dispatcher.add_handler(CommandHandler('fact_cat', fact))
    updater.dispatcher.add_handler(CommandHandler('corona_stats', corona_stats))
    updater.dispatcher.add_handler(CommandHandler('corona_stats_dynamics', corona_stats_dynamics))
    updater.dispatcher.add_handler(CommandHandler('movie', movie))
    updater.dispatcher.add_handler(CommandHandler('joke', joke))
    updater.dispatcher.add_handler(CommandHandler('pokemon', pokemon))
    updater.dispatcher.add_handler(CommandHandler('weather', weather))
    updater.dispatcher.add_handler(CommandHandler('fact_year', fact_year))
    updater.dispatcher.add_handler(CommandHandler('fact_number', fact_number))
    updater.dispatcher.add_handler(CommandHandler('coin', coin))

    updater.dispatcher.add_handler(CallbackQueryHandler(button_corona, pattern='(True|False)'))
    updater.dispatcher.add_handler(CallbackQueryHandler(button_joke, pattern='(Like|Dislike|More jokes)'))

    # on noncommand i.e message - echo the message on Telegram
    updater.dispatcher.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    updater.dispatcher.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    logger.info('Start Bot')
    LOGS = []
    main()
