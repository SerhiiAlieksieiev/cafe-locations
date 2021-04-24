import json
import requests
from geopy import distance
import folium
from flask import Flask
import os


NEAREST_CAFES_AMOUNT = 5


def fetch_coordinates(apikey, place):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    params = {"geocode": place, "apikey": apikey, "format": "json"}
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    found_places = response.json(
    )['response']['GeoObjectCollection']['featureMember']
    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


def read_file(file_path):
    with open(file_path, "r", encoding="CP1251") as my_file:
        cafes_json = my_file.read()
    return json.loads(cafes_json)


def add_distances(cafes, person_longitude, person_latitude):
    cafes_info = []
    for cafe in cafes:
        cafe_name = cafe["Name"]
        cafe_longitude, cafe_latitude = cafe["geoData"]["coordinates"]
        cafe_distance = distance.distance(
            (person_latitude, person_longitude), (cafe_latitude, cafe_longitude)).km

        cafe_info = {
            'title': cafe_name,
            'distance': cafe_distance,
            'latitude': cafe_latitude,
            'longitude': cafe_longitude,
        }
        cafes_info.append(cafe_info)
    return cafes_info


def create_map(nearest_cafes, person_longitude, person_latitude):
    cafes_map = folium.Map(
        location=[person_latitude, person_longitude], zoom_start=12)
    tooltip = "Click me!"
    folium.Marker([person_latitude, person_longitude],
                  popup="My location",
                  tooltip=tooltip,
                  icon=folium.Icon(color="green")).add_to(cafes_map)
    for cafe in nearest_cafes:
        cafe_latitude = cafe["latitude"]
        cafe_longitude = cafe["longitude"]
        title = cafe["title"]
        folium.Marker([cafe_latitude, cafe_longitude],
                      popup=title,
                      tooltip=tooltip).add_to(cafes_map)
    return cafes_map


def get_distance(cafe):
    return cafe['distance']


def open_map():
    with open('index.html') as file:
        return file.read()


if __name__ == '__main__':
    apikey = os.getenv("APIKEY")
    adress = input("Где вы находитесь? ")
    person_coords = fetch_coordinates(apikey, adress)
    person_longitude, person_latitude = person_coords

    cafes = read_file("cafes_list.json")
    cafes_info = add_distances(cafes, person_longitude, person_latitude)
    nearest_cafes = sorted(cafes_info, key=get_distance)[:NEAREST_CAFES_AMOUNT]

    cafes_map = create_map(nearest_cafes, person_longitude, person_latitude)
    cafes_map.save("index.html")

    app = Flask(__name__)
    app.add_url_rule('/', 'map', open_map)
    app.run('0.0.0.0')
