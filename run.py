# -*- coding: utf-8 -*-

import datetime
import json
import logging
import random
from timeit import default_timer as timer

import requests
from bs4 import BeautifulSoup
from imdb import IMDb
from telegram import Bot, Update
from telegram.ext import CallbackContext, CommandHandler, Filters, MessageHandler, Updater

from setup import TOKEN, RAPID_API, OW_API
from utils.utils import *



date = datetime.date.today().strftime("%m-%d-%Y")
bot = Bot(token=TOKEN)
# Enable logging
joke_id = ""
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    text = f"""
Hello, {update.effective_user.first_name}!
Nice to see you here!
If you need help, enter /help command.
"""
    update.message.reply_text(text=text)


def chat_help(update: Update, context: CallbackContext):
    """Send a message when the command /help is issued."""
    text = """
    Supported commands:
/start - start bot
/help - show supported commands
/cat - get random cat photo
/down - get info about 
/movie - get random movie from top-250 IMDb
/weather <city> - get weather info for your city
/pokemon - get info and image of random pokemon
/fact_year <year> - get interesting fact about particular year (default value - 2020)
/fact_number <number> - get integersting fact about number (default value - random < 1000)
/magic_ball - predict your future
"""
    update.message.reply_text(text)


def echo(update: Update, context: CallbackContext):
    """Echo the user message."""
    text = str(update.message.text)
    if text.startswith("/weather "):
        get_weather(text, update.effective_chat['id'])
    else:
        update.message.reply_text(update.message.text)


def get_weather(text, chat_id):
    city = text.replace("/weather ", "")
    text, html_status = weather_response(city)
    if html_status:
        bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')
    else:
        bot.send_message(chat_id=chat_id, text=text)


def error(update: Update, context: CallbackContext):
    """Log Errors caused by Updates."""
    logger.warning(f'Update {update} caused error {context.error}')


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


def pokemon(update: Update, context: CallbackContext):
    text, picture = pokemon_response()
    bot.send_message(chat_id=update.effective_chat['id'], text=text)
    bot.send_photo(chat_id=update.effective_chat['id'], photo=picture)


def fact_year(update: Update, context: CallbackContext):
    data = update.message['text'].split()
    try:
        year = data[1]
    except:
        year = datetime.datetime.now().year
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
                         text="🛠 Random cats images service is down. Try again later.")


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
                         text=f"🛠 These services are down or having problems:\n\n❌ {down_text}")
    else:
        bot.send_message(chat_id=update.effective_chat['id'],
                         text=f"🛠 All services are up!")


def fact_number(update: Update, context: CallbackContext):
    data = update.message['text'].split()
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


def magic_ball(update: Update, context: CallbackContext):
    responses = [
        "It is certain",
        "Without a doubt",
        "You may rely on it",
        "Yes definitely",
        "It is decidedly so",
        "As I see it, yes",
        "Most likely",
        "Yes",
        "Outlook good",
        "Signs point to yes",
        "Reply hazy try again",
        "Better not tell you now",
        "Ask again later",
        "Cannot predict now",
        "Concentrate and ask again",
        "Don't count on it",
        "Outlook not so good",
        "My sources say no",
        "Very doubtful",
        "My reply is no"
    ]
    response = random.choice(responses)
    bot.send_message(chat_id=update.effective_chat['id'], text=response)


def main():
    updater = Updater(workers=32, use_context=True, token=bot.token)

    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('help', chat_help))
    dispatcher.add_handler(CommandHandler('cat', get_random_cat))
    dispatcher.add_handler(CommandHandler('down', get_down_info))
    dispatcher.add_handler(CommandHandler('movie', movie))
    dispatcher.add_handler(CommandHandler('pokemon', pokemon))
    dispatcher.add_handler(CommandHandler('fact_year', fact_year))
    dispatcher.add_handler(CommandHandler('fact_number', fact_number))
    dispatcher.add_handler(CommandHandler('magic_ball', magic_ball))

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