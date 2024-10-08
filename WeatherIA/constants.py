from datetime import datetime
import calendar

MAX_HISTORIC = 96
CITIES_COORDINATES = {
    'Salitre': '-7.285748,-40.457514', 'Campo Sales': '-7.075103,-40.372339', 'Araripe': '-7.211309,-40.138323',
    'Potengi': '-7.091934,-40.027603', 'Assare': '-6.870889,-39.871030', 'Antonina do Norte': '-6.775348,-39.988188',
    'Tarrafas': '-6.684036,-39.758108', 'Altaneira': '-6.998939,-39.738878', 'Nova Olinda': '-7.092372,-39.678686',
    'Santana do Cariri': '-7.185914,-39.737159', 'Farias Brito': '-6.928198,-39.571438', 'Crato': '-7.231216,-39.410477',
    'Juazeiro do Norte': '-7.228166,-39.312093', 'Barbalha': '-7.288738,-39.299320', 'Jardim': '-7.586031,-39.279563',
    'Porteiras': '-7.534501,-39.116856', 'Penaforte': '-7.830278,-39.072340', 'Jati': '-7.688990,-39.005227',
    'Brejo Santo': '-7.488500,-38.987459', 'Abaiara': '-7.349389,-39.033383', 'Milagres': '-7.310940,-38.938627',
    'Mauriti': '-7.382958,-38.771900', 'Barro': '-7.174146,-38.779534', 'Caririaçu': '-7.042127,-39.285435',
    'Granjeiro': '-6.887292,-39.220469', 'Aurora': '-6.943031,-38.969761', 'Lavras da Mangabeira': '-6.752719,-38.965939',
    'Ipaumirim': '-6.789527,-38.718022', 'Baixio': '-6.730631,-38.716898', 'Umari': '-6.644247,-38.699599'
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
    # currentTimeInMilliseconds = round(time.time() * 1000) # future = datetime.fromtimestamp(ms / 1000.0)
    now = datetime.now()
    if now.minute >= 50: # next is 05 minutes
        if now.hour == 23:
            if now.day == calendar.monthrange(2002, 1)[1]: # last day from month
                if now.month == 12: # last month from year
                    future = datetime(now.year + 1, 1, 1, 0, 5, 0)
                else:
                    future = datetime(now.year, now.month + 1, 1, 0, 5, 0)
            else:
                future = datetime(now.year, now.month, now.day + 1, 0, 5, 0)
        else:
            future = datetime(now.year, now.month, now.day, now.hour + 1, 5, 0)
    elif now.minute >= 35:
        future = datetime(now.year, now.month, now.day, now.hour, 50, 0)
    elif now.minute >= 20:
        future = datetime(now.year, now.month, now.day, now.hour, 35, 0)
    else:
        future = datetime(now.year, now.month, now.day, now.hour, 20, 0)
    return int((future - now).total_seconds())