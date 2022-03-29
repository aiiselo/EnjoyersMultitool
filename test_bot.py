from utils.utils import *


def test_weather():
    city = 'Moscow'
    text, html_status = weather_response(city)
    assert 'Moscow' in text
    assert 'Weather' in text
    assert 'Pressure' in text
    assert 'Temperature' in text
    assert html_status is True


def test_pokemon():
    text, picture = pokemon_response()
    assert "Name" in text
    assert "Weight" in text
    assert "Height" in text
    assert ".png" in picture


def test_number():
    response = number_response(1)
    assert "Fact for number 1:" in response


def test_movie():
    text = movie_response()
    assert "Title" in text
    assert "Genre" in text
    assert "Year" in text
    assert "Director" in text
    assert "Runtime" in text
    assert "IMDb rating" in text
    assert "Top 250 rank" in text
    assert "Link" in text


def test_year():
    year = "1941"
    text = year_response(year)
    assert "Year" in text
    assert year in text
