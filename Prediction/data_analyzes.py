import json
import os
import time
import numpy as np
from datetime import datetime
from constants import VERIFY_YEARS_COUNT
from city import CityModel
from sklearn import linear_model
from sklearn import preprocessing
from sklearn import tree
from sklearn import metrics


class DataAnalyzes:
    def __init__(self):
        self.baseDir = os.path.dirname(os.path.realpath(__file__)).replace('\\', '/')
        self.datasetFolder = f'{self.baseDir}/filtered'
        self.totalChapadaAraripe = 0  # Total de clima da chapada do araripe nos ultimos VERIFY_YEARS_COUNT anos
        self.occurredCurrentYear = 0  # Total do ano atual
        self.predictCurrentYear = 0  # Media anual final
        self.predictChapadaAraripe = []  # Previsao de queimadas em cada mes, para a chapada do araripe
        self.occurredChapadaAraripe = []  # Total de clima ocorridos no ano atual, por mes
        self.annualTotalOccurred = {}  # Total de clima ocorridos por ano
        self.cityModels = {}  # Dicionario de cidades
        self.dataChapadaAraripe = {}  # dados dos totais sobre os meses do ano atual}
        self.dataCities = []  # dados a serem enviados pro back-end referentes as cidades (lista de dados de cidaddes)

    def analyze(self):
        self.occurredChapadaAraripe.clear()
        self.predictChapadaAraripe.clear()
        for i in range(0, 12): self.occurredChapadaAraripe.append(0)

        if not os.path.exists(f'{self.baseDir}/release'):
            os.mkdir(f'{self.baseDir}/release')

        self.occurredCurrentYear = 0
        currentYear = datetime.now().year
        for year in range(currentYear - VERIFY_YEARS_COUNT, currentYear + 1):
            if year < currentYear:
                self.annualTotalOccurred[year] = 0
            for fileName in os.listdir(f'{self.datasetFolder}/{year}'):  # fileName Eg:= Salitre.json
                filePath = f'{self.datasetFolder}/{year}/{fileName}'
                fileDataset = open(filePath, 'r', encoding="utf-8")
                if self.datasetFolder == 'request_data':
                    dataset = json.loads(fileDataset.read())['request_data']
                else:
                    dataset = json.loads(fileDataset.read())
                fileDataset.close()

                cityName = fileName[0:fileName.rfind('.')]
                cityModel = CityModel(cityName)
                if cityName in self.cityModels:
                    cityModel = self.cityModels[cityName]
                self.cityModels[cityName] = cityModel

                for arrayFire in dataset:
                    date = arrayFire[0].split('T')[0]
                    segments = date.split('-')
                    cityModel.putFiresData(segments[1], segments[0])
                    if currentYear == int(segments[0]):
                        self.occurredCurrentYear += 1
                    else:
                        self.totalChapadaAraripe += 1

        for cityName in self.cityModels:
            cityModel = self.cityModels[cityName]
            cityModel.calculateMonthlyAverage()
            print(cityModel.name)

            for y in self.annualTotalOccurred:
                if y < currentYear:
                    self.annualTotalOccurred[y] += self.cityModels[cityName].totalPerYears[str(y)]

            for i in range(12):
                base = []
                for items in cityModel.years.items():
                    months = items[1]  # 0 = 2022, 1 = [23, 45, 45,...]
                    base.append(months[i])
                cityModel.monthlyPredict.append(max(self.predictNextNumber(base), 0))
            cityModel.calculateTotals(currentYear)

            count = 0
            for items in cityModel.years.items():
                months = items[1]  # 0 = 2022, 1 = [23, 45, 45,...]
                totalPerYears = cityModel.totalPerYears[items[0]]
                if currentYear != int(items[0]):
                    count += totalPerYears
                else:
                    for i in range(0, 12):
                        self.occurredChapadaAraripe[i] += months[i]
                print(f'{items[0]} -> {months} total: {totalPerYears}')
            print(f'Media -> {cityModel.monthlyAverage}')
            print(f'Media anual da cidade sem contar o atual ano -> {count / VERIFY_YEARS_COUNT}')
            print()

        timestamp = round(time.time() * 1000)
        dateTime = datetime.now().strftime("%Y-%m-%d %H:%M")
        for item in self.cityModels.items():
            print(f'Previsao: {item[1].monthlyPredict} {item[0]}')
            jsonMonths = []
            for index in range(0, 12):
                jsonMonths.append({"fireOccurrences": item[1].years[str(currentYear)][index], "firesPredicted": item[1].monthlyPredict[index]})
            jsonObject = {"timestamp": timestamp, "dateTime": dateTime, 'city': item[0], 'predictionTotal': item[1].predictedCurrentYear, 'occurredTotal': item[1].totalOccurrencesCurrentYear, 'months': jsonMonths}
            self.dataCities.append(jsonObject)
            file = open(f'{self.baseDir}/release/{item[0]}.json', 'w', encoding="utf-8")
            json.dump(jsonObject, file, ensure_ascii=False, indent=4)
            file.close()

        years = {}
        for year in range(currentYear - VERIFY_YEARS_COUNT, currentYear + 1):
            if year == currentYear:
                break
            years[year] = []
            for month in range(0, 12):
                years[year].append(0)
            for cityName in self.cityModels:
                for month in range(0, 12):
                    years[year][month] += self.cityModels[cityName].years[str(year)][month]
        base = []
        for month in range(0, 12):
            base.clear()
            for year in years:
                base.append(years[year][month])
            self.predictChapadaAraripe.append(self.predictNextNumber(base))

        print(f'________________________________________________________________________________________')
        print(f'|\tAno\t\t|\tTotal\t|\tMeses')
        base.clear()
        count = 0
        for y in self.annualTotalOccurred:
            count += self.annualTotalOccurred[y]
            if y != str(currentYear):
                base.append(self.annualTotalOccurred[y])
            print(f'|\t{y}\t|\t{self.annualTotalOccurred[y]}\t|\t{years[y]}')

        self.predictCurrentYear = self.predictNextNumber(base)

        print(f'|\t{currentYear}\t|\t{self.occurredCurrentYear}\t|\t', end='')
        print('[', end='')
        jsonMonths = []
        for i in range(0, 12):
            jsonMonth = {}
            #jsonMonth['number'] = i + 1
            jsonMonth['fireOccurrences'] = self.occurredChapadaAraripe[i]
            jsonMonth['firesPredicted'] = self.predictChapadaAraripe[i]
            jsonMonths.append(jsonMonth)
            print(self.occurredChapadaAraripe[i], end='')
            if i < 11: print(', ', end='')
        print(']')
        print(f'_________________________________________________________________________________________')
        print()

        self.dataChapadaAraripe = {"timestamp": timestamp, "dateTime": dateTime, 'city': "Chapada do Araripe", 'predictionTotal': self.predictCurrentYear, 'occurredTotal': self.occurredCurrentYear, 'months': jsonMonths}
        if not os.path.exists(f'{self.baseDir}/release'):
            os.mkdir(f'{self.baseDir}/release')
        file = open(f'{self.baseDir}/release/Chapada do Araripe.json', 'w', encoding="utf-8")
        json.dump(self.dataChapadaAraripe, file, ensure_ascii=False, indent=4)
        file.close()

        #print(f'Total ocorrido nos ultimos {VERIFY_YEARS_COUNT} anos -> {self.totalChapadaAraripe}')
        print('----------------- PREVISTOS ------------------')
        print(f'PREVISTO MENSAL PARA ESSE ANO -> {self.predictChapadaAraripe}')
        print(f'PREVISTO TOTAL PARA ESSE ANO -> {self.predictCurrentYear}')

    def printModelsStatistics(self):
        print('------------ ESTATISTICAS --------------')
        # occurred = self.occurredChapadaAraripe[i]
        years = {}
        currentYear = datetime.now().year
        for year in range(currentYear - VERIFY_YEARS_COUNT, currentYear + 1):
            if year == currentYear:
                break
            years[year] = []
            for month in range(0, 12):
                years[year].append(0)
            for cityName in self.cityModels:
                for month in range(0, 12):
                    years[year][month] += self.cityModels[cityName].years[str(year)][month]
        modelsName = [
            'POLYNOMIAL_REGRESSION', 'RIDGE_REGRESSION', 'LINEAR_REGRESSION', 'LASSO_REGRESSION',
            'ELASTIC_NET_REGRESSION', 'DECISION_TREE_REGRESSION'  #, 'LOGISTIC_REGRESSION'
        ]
        dictModelsValuesMonths = {}
        for modelName in modelsName:
            base = []
            chapadaPredictionMonths = []
            for month in range(0, 12):
                base.clear()
                for year in years:
                    base.append(years[year][month])
                chapadaPredictionMonths.append(self.predictNextNumber(base, modelName))
            dictModelsValuesMonths[modelName] = chapadaPredictionMonths

        currentMonth = datetime.now().month
        for model in dictModelsValuesMonths.items():
            percentages = []
            percentage = 0
            for i in range(0, currentMonth - 1):
                valuePercentage = int(((self.occurredChapadaAraripe[i] - model[1][i]) / self.occurredChapadaAraripe[i]) * 100)
                percentage += abs(valuePercentage)
                percentages.append(valuePercentage)
            percentage = int(percentage / currentMonth)
            print('-------------------------------------------------------------------------')
            print(f'{model[0]} - Taxa de acerto: {percentage}')
            print(f'predict    {model[1]}')
            print(f'occurred   {self.occurredChapadaAraripe}')
            print(f'percentage {percentages}')

    def predictNextNumber(self, numbers, modelType='LINEAR_REGRESSION'):
        x = np.array(numbers[:-1]).reshape(-1, 1)
        y = np.array(numbers[1:])
        a = np.array([[numbers[-1]]])
        if modelType == 'LOGISTIC_REGRESSION':  # not working
            model = linear_model.LogisticRegression(random_state=len(numbers))
            model.fit(x, y)
            value = model.predict(a)
            return int(value[0])
        if modelType == 'LINEAR_REGRESSION':
            model = linear_model.LinearRegression()
            model.fit(x, y)
            next_number = model.predict(a)
            return int(next_number)
        if modelType == 'POLYNOMIAL_REGRESSION':
            #modelPoly = preprocessing.PolynomialFeatures(degree=2, include_bias=False)
            modelPoly = preprocessing.PolynomialFeatures(interaction_only=True)
            polyFeatures = modelPoly.fit_transform(x)
            modelLinear = linear_model.LinearRegression()
            modelLinear.fit(polyFeatures, y)
            value = modelLinear.predict(polyFeatures)
            return int(value[len(value) - 1])
        if modelType == 'RIDGE_REGRESSION':
            model = linear_model.Ridge(alpha=1.0)
            model.fit(x, y)
            next_number = model.predict(a)
            return int(next_number)
        if modelType == 'LASSO_REGRESSION':
            model = linear_model.Lasso()
            model.fit(x, y)
            next_number = model.predict(a)
            return int(next_number)
        if modelType == 'ELASTIC_NET_REGRESSION':
            model = linear_model.ElasticNet(random_state=0)
            model.fit(x, y)
            next_number = model.predict(a)
            return int(next_number)
        if modelType == 'DECISION_TREE_REGRESSION':
            model = tree.DecisionTreeRegressor(random_state=0)
            model.fit(x, y)
            next_number = model.predict(a)
            return int(next_number)
