import time
from data_analyzes import DataAnalyzes
from utils import getCountDownSeconds, longToString
from sender import Sender
from terra_brasilis import TerraBrasilis
import os

if os.name == 'posix':
    import RPi.GPIO as GPIO

LED_PIN = 26


def update():
    print()
    tbApi = TerraBrasilis()
    while True:                                 # baixar os cookies de forma recursiva em caso de erro
        tbApi.initialize()                      # Download token and cookie from BD Queimadas
        cookie = tbApi.getCookie()              # coockie necessario para acesso a plataforma
        print(f'cookie = {cookie}')
        csrfCookie = tbApi.getCsrf()            # cookie necessario para acesso a plataforma
        print(f'csrf = {csrfCookie}')
        if cookie is not None and csrfCookie is not None: break
        print('Cookies initialization failed! Retrying in 10 seconds...')
        time.sleep(10)
    print('Cookies initialization ok!')
    tbApi.retrieveCities()                     # Baixa os datasets dos anos anteriores se nao existir
    tbApi.updateCurrentData()                 # Baixa o dataset do ano atual e subscreve se existir

    dataAnalyzes = DataAnalyzes()               # Retrieve filtered datasets
    dataAnalyzes.jsonToCsv()                    # converte os datasets baixados para csv
    dataAnalyzes.retrieveCities(False)          # analiza os datasets e cria o objeto "dataCities" a ser enviado ao back-end pela classe Sender e cria os jsons
    dataAnalyzes.runPredictions(False)          # prediz a chapada inteira e cria o objeto "dataChapadaAraripe" a ser enviado ao back-end pela classe Sender
    dataAnalyzes.saveOutputFiles()
    # dataAnalyzes.debugPredictCurrentYear()    # mostrar graficos do ano atual
    # dataAnalyzes.debugPredictPreviousYear()   # mostrar graficos do ano anterior

    sender = Sender(dataAnalyzes.dataChapadaAraripe, dataAnalyzes.dataCities)
    sender.sendDataGeneral()                    # Send request_data for back-end system


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
    finally:
        if isRaspberry: GPIO.output(LED_PIN, GPIO.LOW)
        print()
        print("Finish Prediction System")
