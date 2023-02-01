import json
import urllib
import logging
import urllib.error
import urllib.request
from datetime import datetime
import xml.etree.ElementTree as ET


logger = logging.getLogger()
logger.setLevel(logging.INFO)

exchange_url = 'https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml'
TABLE_NAME = os.environ['TABLE_NAME']

def handler(event, context):
    logger.info('fetching data')
    date, exchange_rates = fetch_exchange_rates()
    update_exchange_rates = date, exchange_rates
    logger.info('job completed')


def fetch_exchange_rates():
    try:
        response = urllib.request.urlopen(exchange_url, timeout=50)
    except urllib.error.URLError as err:
        logger.critical('Failed to download data from %s', exchange_url)
        logger.critical(err)
        sys.exit(1)
    xml_data = response.read()
    data = []
    doc = ET.fromstring(xml_data)
    for i, x in enumerate(doc.find('{http://www.ecb.int/vocabulary/2002-08-01/eurofxref}Cube')):
        daily_data = {
            'date': x.attrib['time'].strip(),
            'rates': {y.attrib['currency'].strip(): y.attrib['rate'].strip() for y in x}
        }
        data.append(daily_data)
        if i == 1:
            break
    if len(data) < 2:
        logger.critical('Failed to read exchange rates from XML: %s', exchange_url)
        sys.exit(1)
    date = data[0]['date']
    latest_rates = data[0]['rates']
    previous_rates = data[1]['rates']
    exchange_rates = {}
    for currency, rate in latest_rates.items():
        if currency not in previous_rates:
            continue
        pre_rate = float(previous_rates[currency])
        diff = float(rate) - pre_rate
        diff = round(diff, 4) or 0.0
        diff_percent = (diff / pre_rate) * 100
        diff_percent = round(diff_percent, 4) or 0.0
        diff = f'+{diff}' if diff > 0 else f'{diff}'
        diff_percent = f'+{diff_percent} %' if diff_percent > 0 else f'{diff_percent} %'
        exchange_rates[currency] = {'value': rate, 'diff': diff, 'diff_percent': diff_percent}
    return date, exchange_rates


def update_exchange_rates(date, exchange_rates):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(TABLE_NAME)
    with table.batch_writer() as writer:
        for currency, data in exchange_rates.items():
            data['id'] = currency
            writer.put_item(Item=data)
        # Dates
        writer.put_item(Item={'id': 'publish_date', 'value': date})
        writer.put_item(Item={'id': 'update_date', 'value': datetime.utcnow().strftime('%Y-%m-%d')})
