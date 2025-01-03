import json
import os
import time

from api import Requester
from constants import CITIES_COORDINATES, MAX_HISTORIC


class WeatherApi:

    def __init__(self):
        self.__url = f'https://api.weatherapi.com/'
        self.__requester = Requester()
        self.arrayToSendWeather = []
        self.arrayToSendProbabillity = []
        self.baseDir = os.path.dirname(os.path.realpath(__file__)).replace('\\', '/')

    def getDaysWithoutRainFromCity(self, cityName):
        for jsonCity in self.arrayToSendWeather:
            if jsonCity['city'] == cityName:
                return jsonCity['daysWithoutRain']
        return 0

    def updateForecast(self):
        print("Updating forecast...")
        self.arrayToSendProbabillity.clear()
        count = 0
        for city in CITIES_COORDINATES.items():
            count += 1
            print(f'{count} - Requesting forecast data for: {city[0]}', end=' ')
            url = f'{self.__url}v1/forecast.json?key=a8856d705d3b4b17b25151225240605&q={city[1]}&aqi=yes'
            forecast = self.downloadData(url)
            if forecast is None:
                # raise Exception(f'Fail request data city {city[0]}')
                print(f'Error while trying request weather data from {city[0]}')
            else:
                self.arrayToSendProbabillity.append(self.retrieveForecastContent(self.getDaysWithoutRainFromCity(city[0]), forecast, city))
            time.sleep(1)
            print()
        if not os.path.exists('release'):
            os.mkdir('release')
        file = open(f'{self.baseDir}/release/AllCitiesForecast.json', 'w', encoding="utf-8")
        json.dump(self.arrayToSendProbabillity, file, ensure_ascii=False, indent=4)
        file.close()

    def updateWeather(self):
        print("Updating weather...")
        self.arrayToSendWeather.clear()
        count = 0
        for city in CITIES_COORDINATES.items():
            count += 1
            print(f'{count} - Requesting weather data for: {city[0]}', end=' ')
            url = f'{self.__url}v1/current.json?key=a8856d705d3b4b17b25151225240605&q={city[1]}&aqi=yes'
            data = self.downloadData(url)
            if data is None:
                # raise Exception(f'Fail request data city {city[0]}')
                print(f'Error while trying request weather data from {city[0]}')
                continue
            else:
                weather = self.retrieveWeatherContent(data, city)
                self.arrayToSendWeather.append(weather)
            time.sleep(1)
            print()
        if not os.path.exists(f'{self.baseDir}/release'):
            os.mkdir(f'{self.baseDir}/release')
        file = open(f'{self.baseDir}/release/AllCitiesWeather.json', 'w', encoding="utf-8")
        json.dump(self.arrayToSendWeather, file, ensure_ascii=False, indent=4)
        file.close()

    def removeRest(self, jsonArray):
        while len(jsonArray) > MAX_HISTORIC:
            jsonArray.pop(0)

    def downloadData(self, url):
        retries = 0
        responseCode = 0
        while responseCode != 200:
            retries += 1
            if retries == 10:
                return None
            content = self.__requester.requestGet(url)
            responseCode = self.__requester.getResponseCode()
            if responseCode == 200:
                return content
            elif retries < 10:
                time.sleep(1)

    def calculateProbability(self, temperature, humidity, daysWithoutRain, uvIndex):
        valueTemperature = max(temperature - 30, 1)     # consider using only high temperatures over 30 degrees
        valueHumidity = 100 - humidity                  # inversely proportional
        weightTemperatureHumidity = ((valueTemperature * valueHumidity) / 1000) * uvIndex
        return min(int((weightTemperatureHumidity**3) * max(1, daysWithoutRain)), 100)

    def retrieveForecastContent(self, daysWithoutRain, forecast, city):
        if not os.path.exists(f'{self.baseDir}/forecast'):
            os.mkdir(f'{self.baseDir}/forecast')
        listForecastHours = json.loads(forecast)['forecast']['forecastday'][0]['hour']
        jsonCity = {'forecast': []}
        for hourData in listForecastHours:
            data = {
                'timestamp': hourData['time_epoch'], 'dateTime': hourData['time'], 'temperature': hourData['temp_c'],
                'humidity': hourData['humidity'], 'uvIndex': hourData['uv'], 'precipitation': hourData['precip_mm'], 'cloud': None, 'carbonMonoxide': None,
                'daysWithoutRain': daysWithoutRain, 'fireRisk': self.calculateProbability(hourData['temp_c'], hourData['humidity'], daysWithoutRain, hourData['uv'])
            }
            jsonCity['forecast'].append(data)
            jsonCity['city'] = city[0]

        filePath = f'{self.baseDir}/forecast/{city[0]}.json'
        file = open(filePath, 'w', encoding="utf-8")
        json.dump(jsonCity, file, ensure_ascii=False, indent=4)
        file.close()
        return jsonCity

    def retrieveWeatherContent(self, weather, city):
        jsonWeather = json.loads(weather)
        region = jsonWeather['location']['region']
        print(f'from {region}. Successful.', end=' ')

        if not os.path.exists(f'{self.baseDir}/weather'):
            os.mkdir(f'{self.baseDir}/weather')

        filePath = f'{self.baseDir}/weather/{city[0]}.json'
        current = jsonWeather['current']
        jsonCity = {}
        if os.path.exists(filePath):
            file = open(filePath, 'r', encoding="utf-8")
            jsonCity = json.loads(file.read())
            file.close()

        if current['precip_mm'] >= 1:
            daysWithoutRain = 0
            hadPrecipitation = True
        else:
            if len(jsonCity) > 0:
                daysWithoutRain = jsonCity['daysWithoutRain']
                hadPrecipitation = jsonCity['hadPrecipitation']
            else:
                daysWithoutRain = 0
                hadPrecipitation = False
        jsonItem = {
            'timestamp': current['last_updated_epoch'], 'dateTime': current['last_updated'], 'city': city[0], 'temperature': current['temp_c'], 'humidity': current['humidity'],
            'uvIndex': current['uv'], 'precipitation': current['precip_mm'], 'cloud': current['cloud'], 'carbonMonoxide': current['air_quality']['co'], 'daysWithoutRain': daysWithoutRain,
            'fireRisk': self.calculateProbability(current['temp_c'], current['humidity'], daysWithoutRain, current['uv'])
        }

        if 'data' not in jsonCity:
            jsonCity['data'] = []
        jsonArray = jsonCity['data']
        jsonArray.append(jsonItem)
        self.removeRest(jsonArray)
        jsonCity['city'] = city[0]
        jsonCity['daysWithoutRain'] = daysWithoutRain
        jsonCity['hadPrecipitation'] = hadPrecipitation
        file = open(filePath, 'w', encoding="utf-8")
        json.dump(jsonCity, file, ensure_ascii=False, indent=4)
        file.close()

        return jsonItem

    def verifyDaysWithoutRain(self):
        for city in CITIES_COORDINATES.items():
            filePath = f'{self.baseDir}/weather/{city[0]}.json'
            jsonCity = {}
            if os.path.exists(filePath):
                file = open(filePath, 'r', encoding="utf-8")
                jsonCity = json.loads(file.read())
                file.close()

            if not jsonCity['hadPrecipitation']:
                jsonCity['daysWithoutRain'] += 1
            file = open(filePath, 'w', encoding="utf-8")
            json.dump(jsonCity, file, ensure_ascii=False, indent=4)
            file.close()
        time.sleep(1)
