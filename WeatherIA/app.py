import traceback
import time
from datetime import datetime
from constants import getCountDownSeconds, longToString
from sender import Sender
from weather_api import WeatherApi
import os
if os.name == 'posix':
    import RPi.GPIO as GPIO
    
LED_PIN = 12

def main(isRaspberry):
    # start first execution
    if isRaspberry:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(LED_PIN, GPIO.OUT)
        GPIO.output(LED_PIN, GPIO.HIGH)
    weather = WeatherApi()
    weather.updateWeather()
    weather.updateForecast()
    print("Sending to back-end...")
    sender = Sender(weather.arrayToSendWeather, weather.arrayToSendProbabillity)
    sender.sendData()
    # end first execution

    # start loop
    awaitingUpdate = False
    while True:
        count = getCountDownSeconds()
        while count > 0:
            now = datetime.now()
            if now.hour == 0 and now.minute == 0 and now.second == 0:
                awaitingUpdate = True
                print()
                if isRaspberry: GPIO.output(LED_PIN, GPIO.HIGH)
                weather.verifyDaysWithoutRain()
            elif now.minute == 5 or now.minute == 20 or now.minute == 35 or now.minute == 50:
                print()
                if isRaspberry: GPIO.output(LED_PIN, GPIO.HIGH)
                weather.updateWeather()
                sender.sendWeather()
                count = getCountDownSeconds()

            elif now.hour == 0 and now.minute == 30 and awaitingUpdate:
                awaitingUpdate = False
                print()
                if isRaspberry: GPIO.output(LED_PIN, GPIO.HIGH)
                weather.updateForecast()
                sender.sendForecast()

            count -= 1
            if isRaspberry:
                GPIO.output(LED_PIN, GPIO.HIGH)
                time.sleep(0.1)
                GPIO.output(LED_PIN, GPIO.LOW)
                time.sleep(0.9)
            else:
                time.sleep(1)
            print(f'\rUpdating in {longToString(count)}', end='', flush=True)

if __name__ == '__main__':
    print("Start Weather System")
    isRaspberry = os.name == 'posix'
    while True:
        try:
            if isRaspberry:
                print('Device recognized as Raspberry platform.')
                print(f'Using GPIO {LED_PIN} for system status.')
            main(isRaspberry)
        except KeyboardInterrupt:
            print()
            print('Interrupted')
            break
        except Exception as e:
            print()
            print(traceback.format_exc())
        finally:		
            if isRaspberry: GPIO.output(LED_PIN, GPIO.LOW)
            print()
        time.sleep(1)
    print("Finish Weather System")
