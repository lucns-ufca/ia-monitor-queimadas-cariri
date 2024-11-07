import json
import time
from api import Requester


class Sender:

    def __init__(self, weather, forecast):
        self.__weather = weather
        self.__forecast = forecast
        #self.__urlWeather = 'https://lucns.io/apps/monitor_queimadas_cariri/weather/weather.php'
        #self.__urlForecast = 'https://lucns.io/apps/monitor_queimadas_cariri/weather/forecast.php'
        self.__urlWeather = 'https://monitorqueimadas.duckdns.org/fire-weather-data'
        self.__urlForecast = 'https://monitorqueimadas.duckdns.org/fire-forecast-data'
        self.__requester = Requester()

    def sendWeather(self):
        print(f'Sending weather data', end=' ')
        self.__sentInternal(self.__urlWeather, json.dumps(self.__weather, ensure_ascii=False))

    def sendForecast(self):
        print(f'Sending forecast data', end=' ')
        self.__sentInternal(self.__urlForecast, json.dumps(self.__forecast, ensure_ascii=False))

    def sendData(self):
        print(f'Sending weather data', end=' ')
        self.sendWeather()
        time.sleep(1)
        #print(f'Sending forecast data', end=' ')
        #self.sendForecast()

    def __sentInternal(self, url, data):
        retries = 0
        success = False
        while not success:
            if retries > 0: print(f'Attempt {retries + 1}', end='. ')
            retries += 1
            if retries == 10:
                print(f'Fail send')
                return
            self.__requester.requestPost(url, data=data)
            responseCode = self.__requester.getResponseCode()
            success = responseCode > 199 and responseCode < 300
            if not success:
                print('Response code: ', responseCode)
                time.sleep(10)
        print(f'Successful.')
