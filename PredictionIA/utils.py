from datetime import datetime
import calendar

INITIAL_DATASET_YEAR = 2014
VERIFY_YEARS_COUNT = datetime.now().year - INITIAL_DATASET_YEAR
CITIES_IDS = {
    'Salitre': '033232311959', 'Campos Sales': '033232302701', 'Araripe': '033232301307', 'Potengi': '033232311207', 'Assaré': '033232301604', 'Antonina do Norte': '033232300804', 'Tarrafas': '033232313252',
    'Altaneira': '033232300606', 'Nova Olinda': '033232309201', 'Santana do Cariri': '033232312106', 'Farias Brito': '033232304301', 'Crato': '033232304202', 'Juazeiro do Norte': '033232307304', 'Barbalha': '033232301901',
    'Jardim': '033232307106', 'Porteiras': '033232311108', 'Penaforte': '033232310605', 'Jati': '033232307205', 'Brejo Santo': '033232302503', 'Abaiara': '033232300101', 'Milagres': '033232308302', 'Mauriti': '033232308104',
    'Barro': '033232302008', 'Caririaçu': '033232303204', 'Granjeiro': '033232304806', 'Aurora': '033232301703', 'Lavras da Mangabeira': '033232307502', 'Ipaumirim': '033232305704', 'Baixio': '033232301802', 'Umari': '033232313708'
}

def longToString(timeCount):
    seconds = timeCount % 60
    if timeCount < 600:
        if seconds < 10:
            return '0' + str(int((timeCount - seconds) / 60)) + ':0' + str(seconds)
        else:
            return '0' + str(int((timeCount - seconds) / 60)) + ':' + str(seconds)
    else:
        if seconds < 10:
            return str(int((timeCount - seconds) / 60)) + ':0' + str(seconds)
        else:
            return str(int((timeCount - seconds) / 60)) + ':' + str(seconds)


def getCountDownSeconds():
    now = datetime.now()
    if now.minute > 0:
        if now.hour == 23:
            if now.day == calendar.monthrange(2002, 1)[1]: # last day from month
                if now.month == 12: # last month from year
                    future = datetime(now.year + 1, 1, 1, 0, 0, 0)
                else:
                    future = datetime(now.year, now.month + 1, 1, 0, 0, 0)
            else:
                future = datetime(now.year, now.month, now.day + 1, 0, 0, 0)
        else:
            future = datetime(now.year, now.month, now.day, now.hour + 1, 0, 0)
        return int((future - now).total_seconds())
    else:
        return 0