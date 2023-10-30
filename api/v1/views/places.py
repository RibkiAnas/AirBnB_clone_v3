#!/usr/bin/python3
"""
place
"""

from re import A
from api.v1.views import app_views
from models.city import City
from models.place import Place
from models.state import State
from models.user import User
from models.amenity import Amenity
from models import storage
import requests
import json
from flask import jsonify, abort, request


@app_views.route('/cities/<string:id>/places', methods=["GET"])
def places_by_city(id):
    """GET Place by city id"""
    city = storage.get(City, id)
    if city is None:
        abort(404)
    else:
        places = city.places
        places_list = []
        for place in places:
            places_list.append(place.to_dict())
    return (jsonify(places_list))


@app_views.route('/places/<string:id>', methods=["GET"])
def place(id):
    """GET Place by id"""
    place = storage.get(Place, id)
    if place is None:
        abort(404)
    return (jsonify(place.to_dict()))


@app_views.route('/places/<string:id>', methods=["DELETE"])
def remove_place(id):
    """REMOVE place by id"""
    place = storage.get(Place, id)
    if place is None:
        abort(404)
    storage.delete(place)
    storage.save()
    return {}, 200


@app_views.route('/cities/<string:id>/places/', methods=["POST"])
def create_place(id):
    """CREATE place by city id"""
    if request.is_json:
        json_place = request.get_json()
        if json_place.get("name") is None:
            abort(400, description="Missing name")
        if json_place.get("user_id") is None:
            abort(400, description="Missing user_id")
        if not storage.get(User, json_place['user_id']):
            abort(404)
        else:
            if storage.get(City, id) is None:
                abort(404)
            json_place["city_id"] = id
            new_place = Place(**json_place)
            new_place.save()
            return new_place.to_dict(), 201
    else:
        abort(400, description="Not a JSON")


@app_views.route('/places/<string:id>', methods=["PUT"])
def update_place(id):
    """UPDATE Place by id"""
    place = storage.get(Place, id)
    if place is None:
        abort(404)
    if request.is_json:
        forbidden = ["id", "created_at", "updated_at", "user_id",
                     "city_id"]
        json_place = request.get_json()
        for k, v in json_place.items():
            if k not in forbidden:
                setattr(place, k, v)
        storage.save()
        return place.to_dict(), 200
    else:
        abort(400, description="Not a JSON")


@app_views.route('/places_search', methods=['POST'],
                 strict_slashes=False)
def search_places():
    """Search places based on JSON in request body"""
    data = request.get_json()
    if not data:
        abort(400, "Not a JSON")
    else:
        states = data.get('states')
        cities = data.get('cities')
        amenities = data.get('amenities')
        places = []
        if not states and not cities and not amenities:
            places_ = storage.all(Place)
            return jsonify([obj.to_dict() for obj in places_.values()])
        if states:
            states_obj = []
            for id in states:
                states_obj.append(storage.get(State, id))
            for state in states_obj:
                for city in state.cities:
                    for place in city.places:
                        places.append(place)
        if cities:
            cities_obj = []
            for id in cities:
                cities_obj.append(storage.get(State, id))
            for city in cities:
                for place in city.places:
                    if place not in places:
                        places.append(place)
        if not places:
            places = storage.all(Place)
            places = [place for place in places.values()]
        if amenities:
            amenity_obj = [storage.get(Amenity, id) for id in amenities]
            i = 0

            while i < len(places):
                place = places[i]
                url = "http://0.0.0.0:5000/api/v1/places/{}/amenities"
                respond = requests.get(url.format(place.id))
                amenity_place = []

                for obj in json.loads(respond.text):
                    amenity_place.append(storage.get(Amenity, obj['id']))

                for a in amenity_obj:
                    if a not in amenity_place:
                        places.pop(i)
                        i -= 1
                        break
                i += 1
        return jsonify([obj.to_dict() for obj in places])
