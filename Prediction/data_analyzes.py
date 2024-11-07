import json
import math
import os
import time
import numpy as np
from datetime import datetime
from matplotlib import pyplot as plt
from sklearn import linear_model
from sklearn import preprocessing
from sklearn import tree
from sklearn.ensemble import RandomForestRegressor
from utils import INITIAL_DATASET_YEAR, CITIES_IDS
from object_models import OccurrenceModel, CityModel


class DataAnalyzes:
    def __init__(self):
        self.base_path = os.path.dirname(os.path.realpath(__file__)).replace('\\', '/')
        self.dataChapadaAraripe = {}  # dados dos totais sobre os meses do ano atual}
        self.dataCities = []  # dados a serem enviados pro back-end referentes as cidades (lista de dados de cidaddes)
        self.cityModels = {}

    def jsonToCsv(self):
        for year in os.listdir(f'{self.base_path}/datasets/json'):
            for city in os.listdir(f'{self.base_path}/datasets/json/{year}'):
                with open(f'{self.base_path}/datasets/json/{year}/{city}', 'r', encoding="utf-8") as input_file:
                    json_array = json.loads(input_file.read())['data']
                    occurrences = {}
                    for json_array2 in json_array:
                        occurrences[json_array2[0]] = OccurrenceModel(None, json_array2[0])
                        occurrences[json_array2[0]].latitude = json_array2[9]
                        occurrences[json_array2[0]].longitude = json_array2[10]

                    output_folder = f'{self.base_path}/datasets/csv/{year}'
                    if not os.path.exists(output_folder): os.makedirs(output_folder)
                    with open(f'{self.base_path}/datasets/csv/{year}/{city.replace('json', 'csv')}', 'w') as output_file:
                        output_file.write('data,latitude,longitude')
                        for item in occurrences.values():
                            output_file.write('\n')
                            output_file.write(f'{item.date},{item.latitude},{item.longitude}')

    def getAllOccurrences(self):
        occurrences = {}
        csv_folder = f'{self.base_path}/datasets/csv'
        for year in os.listdir(f'{csv_folder}'):
            for city in os.listdir(f'{csv_folder}/{year}'):
                with open(f'{csv_folder}/{year}/{city}', 'r', encoding='UTF-8') as input_file:
                    skip = False
                    for line in input_file:
                        if not skip:
                            skip = True
                            continue
                        segments = line.split(',')
                        date_segment = segments[0][0: 7]  # 2014-12
                        if date_segment not in occurrences: occurrences[date_segment] = []
                        occurrences[date_segment].append(OccurrenceModel(city.split('.')[0], segments[0], float(segments[1]), float(segments[2])))

        return occurrences

    def getCurrentYearOccurrences(self):
        current_year_occurred = []
        for month in range(1, datetime.now().month + 1):
            if month < 10: month = f'0{month}'
            total = 0
            for cityModel in self.cityModels.values():
                total += len(cityModel.occurrences_years[f'{datetime.now().year}-{month}'])
            current_year_occurred.append(total)
        return current_year_occurred

    def getCurrentYearPredicted(self, model='DECISION_TREE_REGRESSION'):
        current_year_predicted = []
        for month in range(1, 13):
            if month < 10:
                m = f'0{month}'
            else:
                m = month
            base = []
            for year in range(INITIAL_DATASET_YEAR, datetime.now().year):
                total = 0
                for cityModel in self.cityModels.values(): total += len(cityModel.occurrences_years[f'{year}-{m}'])
                base.append(total)
            predicted = int(self.predict(1, base, model)) * 5
            current_year_predicted.append(predicted)
        return current_year_predicted

    def isNearestOccurrences(self, occurrence, occurrence2):
        if occurrence.latitude == occurrence2.latitude and occurrence.longitude == occurrence2.longitude: return True
        return self.isNearest(occurrence.latitude, occurrence.longitude, occurrence2.latitude, occurrence2.longitude)

    def isNearest(self, lat1, lon1, lat2, lon2):
        radius = 6371  # earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        d = radius * c
        return d <= 1

    def retrieveCities(self, saveFiles):
        for name in CITIES_IDS:
            self.cityModels[name] = CityModel(name)
            self.cityModels[name].initialize()

        # distribuir ocorrencias por mes, dentro de cada respectiva cidade
        occurrences = self.getAllOccurrences()
        for date_segment in occurrences:
            for occurrence in occurrences[date_segment]:
                cityModel = self.cityModels[occurrence.city]
                cityModel.occurrences_years[date_segment].append(occurrence)

        # remover redundancias por coordenadas proximas
        for cityModel in self.cityModels.values():
            for year in range(INITIAL_DATASET_YEAR, datetime.now().year + 1):
                for month in range(1, 13):
                    if month < 10: month = f'0{month}'
                    my_list = []
                    occurrences = cityModel.occurrences_years[f'{year}-{month}']
                    for occurrence in occurrences:
                        nearest = False
                        for occurrence2 in my_list:
                            if self.isNearestOccurrences(occurrence, occurrence2):
                                nearest = True
                                break
                        if nearest: continue
                        my_list.append(occurrence)
                    value = len(cityModel.occurrences_years[f'{year}-{month}'])
                    cityModel.occurrences_years[f'{year}-{month}'] = my_list
                    #print(f'{value}->{len(cityModel.occurrences_years[f'{year}-{month}'])}')

        # predizer os numeros por cidade
        for cityModel in self.cityModels.values():
            for month in range(1, 13):
                base = []
                if month < 10:
                    m = f'0{month}'
                else:
                    m = month
                for year in range(INITIAL_DATASET_YEAR, datetime.now().year):
                    base.append(len(cityModel.occurrences_years[f'{year}-{m}']))
                cityModel.predicted_months[month - 1] = self.predictNextNumber(base)

        # criar os objetos a ser passados posteriormente ao back-end
        timestamp = round(time.time() * 1000)
        dateTime = datetime.now().strftime("%Y-%m-%d %H:%M")
        for cityModel in self.cityModels.values():
            jsonMonths = []
            for month in range(1, 13):
                if month < 10:
                    m = f'0{month}'
                else:
                    m = month
                jsonMonths.append({"fireOccurrences": len(cityModel.occurrences_years[f'{datetime.now().year}-{m}']), "firesPredicted": cityModel.predicted_months[month - 1]})
            jsonObject = {"timestamp": timestamp, "dateTime": dateTime, 'city': cityModel.name, 'predictionTotal': cityModel.getTotalPredicted(), 'occurredTotal': cityModel.getTotalOccurred(), 'monthData': jsonMonths}
            self.dataCities.append(jsonObject)
        if saveFiles:
            if not os.path.exists(f'{self.base_path}/release'): os.makedirs(f'{self.base_path}/release')
            for jsonObject in self.dataCities:
                file = open(f'{self.base_path}/release/{jsonObject['city']}.json', 'w', encoding="utf-8")
                json.dump(jsonObject, file, indent=4)
                file.close()

    def debugPredictCurrentYear(self):
        current_year_occurred = self.getCurrentYearOccurrences()
        models = [
            'RIDGE_REGRESSION', 'LINEAR_REGRESSION', 'LASSO_REGRESSION',
            'ELASTIC_NET_REGRESSION', 'DECISION_TREE_REGRESSION', 'RANDOM_FOREST_REGRESSION'  # POLYNOMIAL_REGRESSION , 'LOGISTIC_REGRESSION'
        ]
        plt.figure(figsize=(10, 6))  # corrigir porcentagens
        for model in models:
            percentage = 0
            current_year_predicted = self.getCurrentYearPredicted(model)
            for i in range(datetime.now().month):
                a = current_year_occurred[i]
                b = current_year_predicted[i]
                if a > b: percentage += int((b / a) * 100)
                else: percentage += int((a / b) * 100)
                #print(f'occurred:{a} predicted:{b} percentage:{value}')
            percentage /= datetime.now().month
            plt.plot(range(1, 13), current_year_predicted, label=f'{model} = {int(percentage)}%', marker='x')
        plt.plot(range(1, len(current_year_occurred) + 1), current_year_occurred, label='Ocorrido', marker='o')
        plt.title('Teste modelo')
        plt.xlabel(f'meses de {datetime.now().year}')
        plt.ylabel('Número de focos')
        plt.legend()
        plt.grid(True)
        plt.show()

    def debugPredictPreviousYear(self):
        back_year = 1
        current_year_occurred = []
        for month in range(1, 13):
            if month < 10: month = f'0{month}'
            total = 0
            for cityModel in self.cityModels.values():
                total += len(cityModel.occurrences_years[f'{datetime.now().year - back_year}-{month}'])
            current_year_occurred.append(total)

        models = [
            'RIDGE_REGRESSION', 'LINEAR_REGRESSION', 'LASSO_REGRESSION',
            'ELASTIC_NET_REGRESSION', 'DECISION_TREE_REGRESSION', 'RANDOM_FOREST_REGRESSION'  # POLYNOMIAL_REGRESSION , 'LOGISTIC_REGRESSION'
        ]
        plt.figure(figsize=(10, 6))  # corrigir porcentagens
        for model in models:
            percentage = 0
            previous_year_predicted = []
            for month in range(1, 13):
                if month < 10:
                    m = f'0{month}'
                else:
                    m = month
                base = []
                for year in range(INITIAL_DATASET_YEAR, datetime.now().year - back_year):
                    total = 0
                    for cityModel in self.cityModels.values(): total += len(cityModel.occurrences_years[f'{year}-{m}'])
                    base.append(total)
                predicted = int(self.predict(1, base, model)) * 5
                previous_year_predicted.append(predicted)
                a = current_year_occurred[month - 1]
                b = previous_year_predicted[month - 1]
                if a > b: percentage += int((b / a) * 100)
                else: percentage += int((a / b) * 100)
            percentage /= 12
            plt.plot(range(1, 13), previous_year_predicted, label=f'{model} = {int(percentage)}%', marker='x')
        plt.plot(range(1, 13), current_year_occurred, label='Ocorrido', marker='o')
        plt.title('Teste modelo')
        plt.xlabel(f'meses de {datetime.now().year - back_year}')
        plt.ylabel('Número de focos')
        plt.legend()
        plt.grid(True)
        plt.show()

    def runPredictions(self, saveFiles):
        current_year_occurred = self.getCurrentYearOccurrences()
        current_year_predicted = self.getCurrentYearPredicted()

        jsonMonths = []
        for i in range(0, 12):
            if i < len(current_year_occurred): occurred = current_year_occurred[i]
            else: occurred = 0
            jsonMonth = {}
            jsonMonth['fireOccurrences'] = occurred
            if i == len(current_year_predicted):
                jsonMonth['firesPredicted'] = 0
            else:
                jsonMonth['firesPredicted'] = current_year_predicted[i]
            jsonMonths.append(jsonMonth)
        timestamp = round(time.time() * 1000)
        dateTime = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.dataChapadaAraripe = {"timestamp": timestamp, "dateTime": dateTime, 'city': "Chapada do Araripe", 'predictionTotal': sum(current_year_predicted), 'occurredTotal': sum(current_year_occurred), 'monthData': jsonMonths}
        if saveFiles:
            if not os.path.exists(f'{self.base_path}/release'): os.makedirs(f'{self.base_path}/release')
            file = open(f'{self.base_path}/release/Chapada do Araripe.json', 'w', encoding="utf-8")
            json.dump(self.dataChapadaAraripe, file, indent=4)
            file.close()

    def saveOutputFiles(self):
        if not os.path.exists(f'{self.base_path}/release'): os.makedirs(f'{self.base_path}/release')
        data = []
        for d in self.dataCities: data.append(d)
        file = open(f'{self.base_path}/release/AllCitiesPredictions.json', 'w', encoding="utf-8")
        json.dump(data, file, indent=4, ensure_ascii=False)
        file.close()
        file = open(f'{self.base_path}/release/ChapadaAraripePredictions.json', 'w', encoding="utf-8")
        json.dump(self.dataChapadaAraripe, file, indent=4, ensure_ascii=False)
        file.close()

    def predictNextNumber(self, y_train):
        return int(self.predict(1, y_train, 'DECISION_TREE_REGRESSION')) * 4

    def predict(self, predictions_count, y_train, model_name):
        time = range(1, predictions_count + 1)
        x_predict = np.array(time).reshape(-1, 1)
        time = range(1, len(y_train) + 1)
        x_train = np.array(time).reshape(-1, 1)

        if model_name == 'LOGISTIC_REGRESSION':  # not working
            model = linear_model.LogisticRegression(random_state=12)
            model.fit(x_train, y_train)
            return model.predict(x_predict)
        elif model_name == 'LINEAR_REGRESSION':
            model = linear_model.LinearRegression()
            model.fit(x_train, y_train)
            return model.predict(x_predict)
        elif model_name == 'POLYNOMIAL_REGRESSION':
            # modelPoly = preprocessing.PolynomialFeatures(degree=2, include_bias=False)
            modelPoly = preprocessing.PolynomialFeatures(interaction_only=True)
            polyFeatures = modelPoly.fit_transform(x_train)
            modelLinear = linear_model.LinearRegression()
            modelLinear.fit(polyFeatures, y_train)
            return modelLinear.predict(polyFeatures)
        elif model_name == 'RIDGE_REGRESSION':
            model = linear_model.Ridge(alpha=1.0)
            model.fit(x_train, y_train)
            return model.predict(x_predict)
        elif model_name == 'LASSO_REGRESSION':
            model = linear_model.Lasso()
            model.fit(x_train, y_train)
            return model.predict(x_predict)
        elif model_name == 'ELASTIC_NET_REGRESSION':
            model = linear_model.ElasticNet(random_state=0)
            model.fit(x_train, y_train)
            return model.predict(x_predict)
        elif model_name == 'DECISION_TREE_REGRESSION':
            model = tree.DecisionTreeRegressor(random_state=0)
            model.fit(x_train, y_train)
            return model.predict(x_predict)
        elif model_name == 'RANDOM_FOREST_REGRESSION':
            model = RandomForestRegressor(random_state=42)
            model.fit(x_train, y_train)
            return model.predict(x_predict)
