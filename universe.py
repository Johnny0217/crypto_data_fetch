# -*- coding: utf-8 -*-
'''
@Time : 2024/5/20 16:33
@Author : Jun
'''
import pandas as pd
import numpy as np
from utils import *
import requests
from utils import *
from urllib.parse import urlunparse, urlencode
import datetime


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


def get_all_known_trading_pairs_coinbase():
    ''' https://api.exchange.coinbase.com/products
    get a list of available currency pairs for trading
    :return:
    '''
    scheme = "https"
    netloc = "api.exchange.coinbase.com"
    path = "/products"
    url = urlunparse((scheme, netloc, path, '', '', ''))
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()  # Python dict
        data_df = pd.DataFrame(data)
        data_df = data_df.sort_values(by=['id'])
        return data_df
    else:
        print(f"Request Failed, Satus code: {response.status_code}")


def coinbase_uni_filter(trading_pairs):
    usdt_pairs = trading_pairs.loc[trading_pairs['quote_currency'] == 'USDT']
    usdt_pairs = usdt_pairs.loc[usdt_pairs['status'] == 'online']
    usdt_pairs = usdt_pairs.loc[usdt_pairs['post_only'] == False]
    usdt_pairs = usdt_pairs.loc[usdt_pairs['trading_disabled'] == False]
    usdt_pairs = usdt_pairs.loc[usdt_pairs['limit_only'] == False]
    usdt_pairs = usdt_pairs.loc[usdt_pairs['cancel_only'] == False]
    return usdt_pairs


if __name__ == '__main__':
    # binance
    bn_trading_pairs = get_exchangeInfo('SPOT', 'USDT')
    bn_usdt_pairs = bn_trading_pairs.loc[bn_trading_pairs['status'] == 'TRADING']
    # coinbase
    coinbase_trading_pairs = get_all_known_trading_pairs_coinbase()
    coinbase_usdt_pairs = coinbase_uni_filter(coinbase_trading_pairs)
    bn_symbols = bn_usdt_pairs['symbol'].values
    coinbase_symbols = coinbase_usdt_pairs['id'].map(lambda x: x.replace('-', '')).values
    # intersection
    today = datetime.date.today()
    date = int(today.strftime("%Y%m%d"))    # today's date
    intersect_pools = pd.Series(np.intersect1d(bn_symbols, coinbase_symbols))
    intersect_pools.to_csv(f'./daily_pool_save/{date}_uni.csv')
    # past uni
    # uni = pd.DataFrame(index=[20240519], columns=past_uni_list.iloc[:, 0].values.tolist())
    # uni = uni.fillna(1)
    uni = pd.read_csv('uni.csv', index_col=0)
    # append new trading list for today
    new_trading_list = pd.read_csv(f'./daily_pool_save/{date}_uni.csv', index_col=0).iloc[:, 0].values.tolist()
    # today's pool info
    new_index = date
    new_row = pd.DataFrame(0, index=[new_index], columns=uni.columns)
    uni = pd.concat([uni, new_row])
    for new_trading_item in new_trading_list:
        if new_trading_item not in uni.columns:
            # 添加新列，并填充之前的值为0，今天的值为1
            uni[new_trading_item] = 0
            uni.loc[new_index, new_trading_item] = 1
        else:
            uni.loc[new_index, new_trading_item] = 1
    uni.to_csv('uni.csv')
    print('debug point here')
