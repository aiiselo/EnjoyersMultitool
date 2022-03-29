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
