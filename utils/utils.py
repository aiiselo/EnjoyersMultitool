import json
import random

import requests
from imdb import IMDb

from setup import TOKEN, RAPID_API, OW_API

openweather_url = "http://api.openweathermap.org/data/2.5/weather?q="


def weather_response(city):
    city_request = requests.get( openweather_url + city + OW_API )
    status_html = False
    try:
        city_dict = city_request.json()
        request_code = city_dict["cod"]

        if request_code != 200:
            return city_dict["message"], status_html
        else:
            city_name = city_dict["name"]
            country_name = city_dict["sys"]["country"]
            city_weather = city_dict["weather"][0]["description"]
            city_temperature = str(int( float( city_dict["main"]["temp"] ) - 273.15 + 0.5 ) )
            city_pressure = str(city_dict["main"]["pressure"] )
            city_humidity = str(city_dict["main"]["humidity"] )
            city_wind = str( city_dict["wind"]["speed"] )

            weather_text = "<b>City: </b>{} - {}\n<b>Weather: </b>{}\n<b>Temperature: </b>{}°C\n" \
                           "<b>Pressure: </b>{}\n<b>Humidity: </b>{}%\n<b>Wind: </b>{} m/s".format(
                city_name, country_name, city_weather, city_temperature, city_pressure, city_humidity,
                city_wind)
            status_html = True
            return weather_text, status_html
    except:
        return "🛠 Weather service is down. Try again later.", status_html


def pokemon_response():
    num = random.randint(1, 807)
    pokemon_info = requests.get( f'https://pokeapi.co/api/v2/pokemon/{num}/' )
    pokemon_info = json.loads(pokemon_info.text )
    text = f"""
                Name: {pokemon_info['name'].capitalize()}
                Height: {pokemon_info['height']}
                Weight: {pokemon_info['weight']}
                Type: {pokemon_info['types'][0]['type']['name']}
                """
    return text, pokemon_info['sprites']['front_default']

def number_response(number):
    url = f"https://numbersapi.p.rapidapi.com/{number}/math"
    querystring = {"fragment": "true", "json": "true"}
    headers = {
        'x-rapidapi-host': "numbersapi.p.rapidapi.com",
        'x-rapidapi-key': RAPID_API
    }
    response = requests.request("GET", url, headers=headers, params=querystring )
    response = json.loads(response.text)
    response = f"Fact for number {number}: " + response["text"].capitalize()
    return response    return text, pokemon_info['sprites']['front_default']


def movie_response():
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
    return text


def year_response(year):
    url = f"https://numbersapi.p.rapidapi.com/{year}/year"
    querystring = {"fragment": "true", "json": "true"}
    headers = {
        'x-rapidapi-host': "numbersapi.p.rapidapi.com",
        'x-rapidapi-key' : RAPID_API
    }
    response = requests.request("GET", url, headers = headers, params = querystring)
    response = json.loads(response.text)
    response = f"Year {year}: " + response["text"].capitalize()
    return response
