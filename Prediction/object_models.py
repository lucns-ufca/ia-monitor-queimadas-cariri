import calendar
from datetime import datetime
from utils import INITIAL_DATASET_YEAR


class CityModel:

    def __init__(self, name):
        self.name = name
        self.fires = 0
        self.occurrences_years = {}
        self.predicted_months = []

    def initialize(self):
        for year in range(INITIAL_DATASET_YEAR, datetime.now().year + 1):
            for month in range(1, 13):
                self.predicted_months.append(0)
                if month < 10: month = f'0{month}'
                self.occurrences_years[f'{year}-{month}'] = []


    def firesCount(self):
        return self.fires

    def getTotalOccurred(self):
        total = 0
        for month in range(1, 13):
            if month < 10: month = f'0{month}'
            total += len(self.occurrences_years[f'{datetime.now().year}-{month}'])
        return total

    def getTotalPredicted(self):
        total = 0
        for i in self.predicted_months: total += i
        return total


class OccurrenceModel:

    def __init__(self, city=None, date=None, lat=0, lon=0):
        self.city = city
        self.date = date
        self.fires = 0
        self.temperature = 0
        self.humidity = 0
        self.radiation = 0
        self.latitude = lat
        self.longitude = lon

    def refactor(self):
        year = self.date[0: 4]  # 2014-12-09T16:33:00.000Z
        month = self.date[5: 7]
        last_month_day = calendar.monthrange(int(year), int(month))[1]
        self.date = f'{year}-{month}-{last_month_day}T23:59:59.000Z'
        if self.fires == 0: return
        self.temperature /= self.fires
        self.humidity /= self.fires
        self.radiation /= self.fires
