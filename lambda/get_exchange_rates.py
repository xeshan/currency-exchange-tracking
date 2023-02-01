
import os
import json
import logging

import boto3

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

TABLE_NAME = os.environ['TABLE_NAME']


def handler(event, context):
    items = read_from_db()
    if not items:
        LOGGER.info('No data available')
        error = "No data available, please try later"
        return {'statusCode': 200, 'body': json.dumps({'error': error}, indent=4)}
    LOGGER.info('Constructing response')
    response = {'update_at': 'N/A', 'created_at': 'N/A', 'base_currency': 'EUR', 'exchange_rates': []}
    for item in items:
        if item['id'] in ('update_at', 'created_at'):
            response[item['id']] = item['value']
        else:
            data = {'currency':          item['id'],
                    'rate':              item['value'],
                    'change':            item['diff'],
                    'change_percentage': item['diff_percent']}
            response['exchange_rates'].append(data)
    # Sort list by currency name
    response['exchange_rates'] = sorted(response['exchange_rates'], key=lambda x: x['currency'])
    # Return response
    return {'statusCode': 200, 'body': json.dumps(response, indent=4)}


def read_from_db():
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(TABLE_NAME)
    # Read table data
    response = table.scan()
    items = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response['Items'])
    return items
