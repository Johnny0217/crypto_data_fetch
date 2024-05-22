# -*- coding: utf-8 -*-
'''
@Time : 2024/5/20 15:52
@Author : Jun
'''

# -*- coding: utf-8 -*-
'''
@Time : 2024/3/5 13:59
@Author : Jun
'''

import pandas as pd
import numpy as np
from binance.spot import Spot
import configparser
import requests
import json
from utils import *
from urllib.parse import urlunparse, urlencode
import urllib.parse
from datetime import datetime
from tqdm import tqdm
import time
import pytz
import matplotlib.pyplot as plt

'''
API Doc
https://github.com/binance/binance-spot-api-docs/blob/master/rest-api_CN.md
all response from public binance RESTful API -> json format
[a1, a2, a3, ...] -> a1 represents the earliest time
UNIX time -> ms

kline interval
1s 1m 3m 5m 15m 30m 1h 2h 4h 6h 8h 12h 1d 3d 1w 1M
'''


def check_connection():
    scheme = "https"
    net_loc = 'api.binance.com'
    path = '/api/v3/ping'
    url = urlunparse((scheme, net_loc, path, '', '', ''))
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()  # Python dict
        print(f'{log_info()} connection is good!')
    else:
        print(f"{log_info()} Request Failed, Satus code: {response.status_code}")


def get_ob_depth(symbol: str, limit: int = 10):
    ''' GET /api/v3/depth
    limit       weight
    1-100       5
    101-500     25
    501-1000    50      limit by default = 100 max 5000 [5, 10, 20, 50, 100, 500, 1000, 5000]
    1001-5000   250     limit = 100 -> returns all order book (extremely large volume of data)
    '''
    scheme = "https"
    net_loc = 'api.binance.com'
    path = '/api/v3/depth'
    query_params = urlencode({'symbol': f'{symbol}', 'limit': f'{limit}'})
    url = urlunparse((scheme, net_loc, path, '', query_params, ''))
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()  # Python dict
        data = pd.DataFrame(data).sort_values(by=['lastUpdateId'])
        return data
    else:
        print(f"{log_info()} Request Failed, Satus code: {response.status_code}")


def get_aggTrades(symbol: str, startTime: int = None, endTime: int = None, limit: int = 1000, fromId: int = None):
    '''
    get_aggTrades('BTCUSDT', limit=3, fromId=69180)
    get_aggTrades('BTCUSDT', start, end, limit=1000)
    :param symbol: BTCUSDT / ETHUSDT
    :param startTime: unix ms
    :param endTime: unix ms
    :param limit: max 1000
    :param fromId: not used
    '''
    scheme = "https"
    net_loc = 'api.binance.com'
    path = '/api/v3/aggTrades'
    query_params = {'symbol': f'{symbol}', 'limit': f'{limit}'}
    if startTime is not None:
        query_params['startTime'] = f'{startTime}'
        query_params['endTime'] = f'{endTime}'
    if fromId is not None:
        query_params['fromId'] = f'{fromId}'
    query = urlencode(query_params)
    url = urlunparse((scheme, net_loc, path, '', query, ''))
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if type(data) == list:
            if len(data) == 0:
                print('Request response is empty')
                return
            else:
                data = pd.DataFrame(data)
                data['datetime_utc'] = pd.to_datetime(data['T'], unit='ms')
                bj_tz = pytz.timezone('Asia/Shanghai')
                data['datetime_bj'] = data['datetime_utc'].dt.tz_localize('UTC').dt.tz_convert(bj_tz)
                data = data.sort_values(by=['datetime_bj'])
                return data
    else:
        print(f"{log_info()} Request Failed, Satus code: {response.status_code}")


def get_klines(symbol, interval, start):
    '''
    get_klines('BTCUSDT', '1d', f'{beijing_datetime_to_unix('2017-08-17 08:00:00')}')
    :param symbol:
    :param interval:
    :param start:
    :return:
    '''
    kline_url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&startTime={start}'
    response = requests.get(kline_url)
    if response.status_code == 200:
        data = response.json()
        data = pd.DataFrame(data)
        headers = ['open_unix', 'open', 'high', 'low', 'close', 'volume', 'close_unix', 'amount', 'num_trades',
                   'taker_volume', 'taker_amount', 'ignore']
        data.columns = headers
        data['open_UTC'] = pd.to_datetime(data['open_unix'], unit='ms')
        data['close_UTC'] = pd.to_datetime(data['close_unix'], unit='ms')
        data = data.drop(columns=['ignore', 'open_unix', 'close_unix'])
        return data
    else:
        print('Failed!')


def get_historical_trades(symbol, id, limit=5):
    historical_trades_url = f'https://api.binance.com/api/v3/historicalTrades?symbol={symbol}&fromId={id}&limit={limit}'
    response = requests.get(historical_trades_url)
    if response.status_code == 200:
        data = response.json()
        data = pd.DataFrame(data)
        data['datetime_utc'] = pd.to_datetime(data['time'], unit='ms')
        bj_tz = pytz.timezone('Asia/Shanghai')
        data['datetime_bj'] = data['datetime_utc'].dt.tz_localize('UTC').dt.tz_convert(bj_tz)
        data = data.sort_values(by=['datetime_bj'])
        return data
    else:
        print('Failed!')


def get_exchangeInfo(permissions, quoteAsset):
    '''
    :param permissions: SPOT / MARGIN / LEVERAGED
    :return: current exchange trading rules and symbol information
    '''
    historical_trades_url = f'https://api.binance.com/api/v3/exchangeInfo?permissions={permissions}'
    response = requests.get(historical_trades_url)
    if response.status_code == 200:
        data = response.json()
        data = data['symbols']
        data = pd.DataFrame(data)
        data = data.loc[data['quoteAsset'] == f'{quoteAsset}', :]
        return data
    else:
        print('Connection Failed')


def api_time_analysis():
    api = pd.read_csv('symbol_api_start_time_utc.csv', index_col=0)
    api.columns = ['utc_time']
    api = api.sort_values(by=['utc_time'])
    api['year'] = api['utc_time'].str.slice(0, 4)
    yearly_count = api.groupby(['year']).count()
    yearly_count['cumu'] = yearly_count['utc_time'].cumsum()
    fig = plt.figure(figsize=(10, 5))
    ax = fig.add_subplot(1, 1, 1)
    ax.set_title('Binance USDT(quoteAsset) trading-pair numbers')
    x = yearly_count.index.values
    ax.bar(x, height=yearly_count['utc_time'], width=0.8, color='orange')
    ax1 = ax.twinx()
    ax1.plot(x, yearly_count['cumu'], label='cumulative numbers', color='g')
    return


if __name__ == '__main__':
    start = beijing_datetime_to_unix('2024-03-07 08:00:00')
    end = beijing_datetime_to_unix('2024-03-08 08:00:00')

    # get_klines('BTCUSDT', '1d', start)
    # get_klines('BTCUSDT', '1d', start)
    # get_aggTrades('BTCUSDT', limit=3, fromId=69180)
    # get_aggTrades('BTCUSDT', start, end, limit=1000)
    # get_historical_trades('BTCUSDT', 69100, 100)

    bn_pool = get_exchangeInfo('SPOT', 'USDT')
    pool = bn_pool.loc[bn_pool['status'] == 'TRADING']






    print('debug point here')
    # trading_pairs = pd.read_csv('binance-spot-tradingpairs.csv', index_col=0)
    # api_time_analysis()

    # from binance.spot import Spot

    # client = Spot()

    # print(client.klines("BTCUSDT", '1m'))
    # # timeZone = 0 ---> UTC
    # data = client.klines(symbol='BTCUSDT', interval='1m', startTime=1499040000000, endTime=1599644799999, timeZone='0')
    # client.klines(symbol='BTCUSDT', interval='1d')
    # df = client.klines(symbol='AAVEUPUSDT', interval='1d')
    # # print(client.klines("BNBUSDT", "1h", limit=10))
    # print(client.lines("BNBUSDT", "1h", limit=10))


    print('DEBUG POINT HERE')