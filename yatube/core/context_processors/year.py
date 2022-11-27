import datetime as dt


def year(request):
    """Добавляет переменную с текущим годом."""
    return {
        'year': int(dt.date.today().strftime('%Y'))
    }
