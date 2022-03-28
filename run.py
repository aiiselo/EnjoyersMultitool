# -*- coding: utf-8 -*-

import logging
import json
import random
from timeit import default_timer as timer
import requests
import datetime

from bs4 import BeautifulSoup
from imdb import IMDb
from setup import TOKEN, RAPID_API
from telegram import Bot, Update
from telegram.ext import CallbackContext, CommandHandler, Filters, MessageHandler, Updater
from classes import Logs


date = datetime.date.today().strftime("%m-%d-%Y")
bot = Bot(token=TOKEN)
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
/movie - get random movie from top-250 IMDb
/pokemon - get info and image of random pokemon
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
def get_random_cat(update: Update, context: CallbackContext):
    for i in range(5):
        try:
            pic_request = requests.get(url="https://api.thecatapi.com/v1/images/search")
            pic_dict = pic_request.json()[0]
            pic_url = pic_dict['url']

            bot.send_photo(chat_id=update.effective_chat['id'], photo=pic_url)
        except:
            continue
        else:
            break
    else:
        bot.send_message(chat_id=update.effective_chat['id'],
                         text="🛠 Сервис по выдаче рандомных котиков приуныл. Попробуйте позже.")

@add_log
def get_down_info(update: Update, context: CallbackContext):
    url_uptime = "https://servicesdown.com"
    uptime_request = requests.get(url_uptime).content
    uptime_soup = BeautifulSoup(uptime_request, 'html')
    status_uptime = uptime_soup.find_all("div", {"class": "flex flex-col items-center"})
    down_list = []

    for element in status_uptime:
        if element.find("div", {"class": "bg-red-200 text-sm opacity-75 text-red-800 px-2 rounded text-center"}):
            down_list.append(element.div.img.get('alt'))

    down_text = "\n❌ ".join(down_list)

    if down_list:
        bot.send_message(chat_id=update.effective_chat['id'],
                         text=f"🛠 Данные сервисы испытывают проблемы:\n\n❌ {down_text}")
    else:
        bot.send_message(chat_id=update.effective_chat['id'],
                         text=f"🛠 Все сервисы в строю!")

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
    response = random.choice(['Орёл', 'Решка'])
    bot.send_message(chat_id=update.effective_chat['id'], text=response)


def main():
    updater = Updater(workers=32, use_context=True, token=bot.token)

    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('help', chat_help))
    dispatcher.add_handler(CommandHandler('history', history))
    dispatcher.add_handler(CommandHandler('test', test))
    dispatcher.add_handler(CommandHandler('cat', get_random_cat))
    dispatcher.add_handler(CommandHandler('down', get_down_info))
    dispatcher.add_handler(CommandHandler('movie', movie))
    dispatcher.add_handler(CommandHandler('pokemon', pokemon))
    dispatcher.add_handler(CommandHandler('fact_year', fact_year))
    dispatcher.add_handler(CommandHandler('fact_number', fact_number))
    dispatcher.add_handler(CommandHandler('coin', coin))

    # on noncommand i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dispatcher.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.


if __name__ == '__main__':
    logger.info('Start Bot')
    LOGS = []
    main()