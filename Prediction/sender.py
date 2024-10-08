import json
import time
import os
from api import Requester

class Sender:

    def __init__(self, dataChapadaAraripe, dataCities):
        self.__dataChapadaAraripe = dataChapadaAraripe
        self.__dataCities = dataCities
        self.__url = 'https://lucns.io/apps/monitor_queimadas_cariri/prediction/predictions.php'
        self.__requester = Requester()
        self.baseDir = os.path.dirname(os.path.realpath(__file__)).replace('\\', '/')

    def sendDataGeneral(self):
        print('Sending general request_data')
        data = []
        #request_data.append(self.__dataChapadaAraripe)
        for d in self.__dataCities: data.append(d)

        file = open(f'{self.baseDir}/release/AllCitiesPredictions.json', 'w', encoding="utf-8")
        json.dump(data, file, ensure_ascii=False, indent=4)
        file.close()

        self.__sentInternal(self.__url, json.dumps(data))

    def sendData(self):
        print(f'Sending request_data from: {self.__dataChapadaAraripe["city"]}', end=' ')
        self.__sentInternal(self.__url, json.dumps(self.__dataChapadaAraripe))
        for data in self.__dataCities:
            print(f'Sending request_data from: {data["city"]}', end=' ')
            self.__sentInternal(self.__url, json.dumps(data))
            time.sleep(1)

    def __sentInternal(self, url, data):
        retries = 0
        success = False
        while not success:
            if retries > 0: print(f'Attempt {retries + 1}', end='. ')
            retries += 1
            if retries == 10:
                print(f'Fail send request_data from {data["city"]}')
                return
            self.__requester.requestPost(url, data=data)
            responseCode = self.__requester.getResponseCode()
            success = responseCode > 199 and responseCode < 300
            if not success:
                print('Response code: ', responseCode)
                time.sleep(10)
        print(f'Successful.')
