# -*- coding: utf-8 -*-
'''
@Time : 2024/5/20 15:27
@Author : Jun
'''

from datetime import datetime
import importlib
import pandas as pd
import numpy as np
from scipy.stats import norm
import numba
import warnings
import os
import pytz

warnings.filterwarnings('ignore')
from numpy.lib import stride_tricks, pad
from joblib import Parallel, delayed
from tqdm import tqdm


def beijing_datetime_to_unix(date_time_str: str):
    '''
    Beijing_datetime  '2023-10-12 00:00:00' -> UTC timezone -> UNIX ms
    '''
    beijing_tz = pytz.timezone('Asia/Shanghai')
    utc_tz = pytz.utc
    date_time_obj_beijing = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S')
    date_time_obj_utc = beijing_tz.localize(date_time_obj_beijing).astimezone(utc_tz)
    timestamp_ms = int(date_time_obj_utc.timestamp() * 1000)
    return timestamp_ms


def check_path(path):
    if not os.path.exists(path):
        os.makedirs(path)
    else:
        return


def mk_data_path_from_vary_source(source):
    project_path = os.getcwd()
    save_file = 'data'
    save_path = os.path.join(project_path, save_file, source)
    check_path(save_path)
    return save_path


def log_info():
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")
