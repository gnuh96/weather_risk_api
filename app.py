from flask import Flask, request, make_response
from flask_restful import Resource, Api
from flask_cors import CORS
import os
import prediction_tornado

import openmeteo_requests
import requests_cache
from retry_requests import retry
import pandas as pd

app = Flask(__name__)
cors = CORS(app, origins='*', expose_headers=['Content-Type'])
api = Api(app)

cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)


@app.teardown_appcontext
def teardown_sessions(exception=None):
    cache_session.close()
    retry_session.close()


class Test(Resource):
    def get(self):
        return 'Welcome to, Test App API!'

    def post(self):
        try:
            value = request.get_json()
            if (value):
                return {'Post Values': value}, 201

            return {"error": "Invalid format."}

        except Exception as error:
            return {'error': error}


class WeatherUtils:
    @staticmethod
    def get_weather_data(date, latitude, longitude):
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": ["temperature_2m_min", "rain_sum", "wind_speed_10m_max"],
            "timezone": "America/New_York",
            "start_date": date,
            "end_date": date  # Assuming you want the end date to be the same as the start date
        }
        responses = openmeteo.weather_api(url, params=params)

        # Process first location. Add a for-loop for multiple locations or weather models
        response = responses[0]

        # Process daily data. The order of variables needs to be the same as requested.
        daily = response.Daily()
        daily_temperature_2m_min = daily.Variables(0).ValuesAsNumpy()
        daily_rain_sum = daily.Variables(1).ValuesAsNumpy()
        daily_wind_speed_10m_max = daily.Variables(2).ValuesAsNumpy()

        daily_data = {
            "date": [str(d) for d in pd.date_range(
                start=pd.to_datetime(daily.Time(), unit="s"),
                end=pd.to_datetime(daily.TimeEnd(), unit="s"),
                freq=pd.Timedelta(seconds=daily.Interval()),
                inclusive="left"
            )],
            "temperature_2m_min": daily_temperature_2m_min.tolist(),
            "rain_sum": daily_rain_sum.tolist(),
            "wind_speed_10m_max": daily_wind_speed_10m_max.tolist(),
        }

        return {"start_date": date, "latitude": latitude, "longitude": longitude, "response": daily_data}


class GetWeather(Resource):
    def get(self):
        date = request.args.get('date', '2023-11-20')
        latitude = float(request.args.get('latitude', 0))
        longitude = float(request.args.get('longitude', 0))

        weather_data = WeatherUtils.get_weather_data(date, latitude, longitude)
        return {"message": "Test", **weather_data}

    def post(self):
        return {"error": "Invalid Method."}


class GetPredictionOutput(Resource):
    def get(self):
        date = request.args.get('date', '2023-11-20')
        latitude = float(request.args.get('latitude', 0))
        longitude = float(request.args.get('longitude', 0))
        weather_data = WeatherUtils.get_weather_data(
            date, latitude, longitude)
        predictInput = {
            "TEMP_MIN": float(weather_data["response"]["temperature_2m_min"][0]),
            "RAIN_SUM": float(weather_data["response"]["rain_sum"][0]),
            "WINDSPEED": float(weather_data["response"]["wind_speed_10m_max"][0])
        }
        print(predictInput)
        try:
            predict = prediction_tornado.predict_tornado(predictInput)
            predictOutput = predict
            return {**predictInput, 'predict_Tornado': predictOutput}

        except Exception as error:
            return {'error': error}

    def post(self):
        try:
            data = request.get_json()
            print(data)
            predict = prediction_tornado.predict_tornado(data)
            predictOutput = predict
            return make_response({'predict': predictOutput}, 200)

        except Exception as error:
            return make_response({'error': str(error)}, 500)


api.add_resource(Test, '/')
api.add_resource(GetPredictionOutput, '/predict')
api.add_resource(GetWeather, '/weather')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
