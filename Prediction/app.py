import time
from data_analyzes import DataAnalyzes
from constants import getCountDownSeconds, longToString
from sender import Sender
from terra_brasilis import TerraBrasilis
import os
if os.name == 'posix':
    import RPi.GPIO as GPIO
    
LED_PIN = 26

def update():
    print()
    tbApi = TerraBrasilis()
    while True:
        tbApi.initialize()  # Download token and cookie from BD Queimadas
        cookie = tbApi.getCookie()
        # print(f'cookie = {cookie}')
        csrfCookie = tbApi.getCsrf()
        # print(f'csrf = {csrfCookie}')
        if cookie is not None and csrfCookie is not None: break
        print('Cookies initialization failed! Retrying in 10 seconds...')
        time.sleep(10)
    print('Cookies initialization ok!')
    tbApi.retrieveCities()  # Datasets downloads (THIS OPERATION TAKE TENS MINUTES)
    #tbApi.updateCurrentData()      # Dataset download from current year
    tbApi.removeDuplicities()      # Duplicities remover

    dataAnalyzes = DataAnalyzes()  # Retrieve filtered datasets
    dataAnalyzes.analyze()  # Analyzes on datasets for storage request_data
    dataAnalyzes.printModelsStatistics()

    sender = Sender(dataAnalyzes.dataChapadaAraripe, dataAnalyzes.dataCities)
    #sender.sendDataGeneral()  # Send request_data for back-end system

def main(isRaspberry):
    if isRaspberry:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(LED_PIN, GPIO.OUT)
        GPIO.output(LED_PIN, GPIO.HIGH)
    update()
    awaitingUpdate = False
    while True:
        if isRaspberry:
            GPIO.output(LED_PIN, GPIO.HIGH)
        if awaitingUpdate: update()
        awaitingUpdate = False
        count = getCountDownSeconds()
        while count > 0:
            count -= 1
            if count == 0: awaitingUpdate = True
            if isRaspberry:
                GPIO.output(LED_PIN, GPIO.HIGH)
                time.sleep(0.1)
                GPIO.output(LED_PIN, GPIO.LOW)
                time.sleep(0.9)
            else:
                time.sleep(1)
            print(f'\rUpdating in {longToString(count)}', end='', flush=True)

if __name__ == '__main__':
    print("Start Prediction System")
    isRaspberry = os.name == 'posix'
    try:
        if isRaspberry:
            print('Device recognized as Raspberry platform.')
            print('Using GPIO 36 for Prediction system status.')
        main(isRaspberry)
    except KeyboardInterrupt:
        print()
        print('Interrupted')
    except Exception as e:  
        print()      
        print(str(e))
    finally:		
        if isRaspberry: GPIO.output(LED_PIN, GPIO.LOW)
        print()
        print("Finish Prediction System")
