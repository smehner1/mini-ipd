#!/usr/bin/python3

import sys
import time
import threading
import numpy as np
import pandas as pd

from typing import Tuple
from clickhouse_driver import Client


__author__ = 'Max Bergmann'


MITTELERDE: str = '/home/max/WORK/masterthesis/pipeline/data/'
BITHOUSE: str = '/home/bergmmax/WORK/masterthesis/pipeline/data/'
DIR: str = '/home/bergmmax/WORK/masterthesis/parameter_analyse'

# overall number of possible IPs
COMPLETE_ADDRESSSPACE: int = 2**32
NUM_KNOWN_AS: int = 5  # SELECT COUNT(DISTINCT prefix_asn) FROM parameter_study
CLIENT: Client = Client('127.0.0.1', database='max')


class Spinner:
    '''class for loading spinner in CLI'''
    busy = False
    delay = 0.1

    @staticmethod
    def spinning_cursor():
        while 1:
            for cursor in '|/-\\':
                yield cursor

    def __init__(self, delay=None):
        self.spinner_generator = self.spinning_cursor()
        if delay and float(delay):
            self.delay = delay

    def spinner_task(self):
        while self.busy:
            sys.stdout.write(next(self.spinner_generator))
            sys.stdout.flush()
            time.sleep(self.delay)
            sys.stdout.write('\b')
            sys.stdout.flush()

    def __enter__(self):
        self.busy = True
        threading.Thread(target=self.spinner_task).start()

    def __exit__(self, exception, value, tb):
        self.busy = False
        time.sleep(self.delay)
        if exception is not None:
            return False


def get_parametrizations() -> pd.DataFrame:
    '''
    return DataFrame including all parametrizations with combining all factor values

    Returns
    -------
    frame (DataFrame): DataFrame that has each parameter as column and includes all combinations
    '''
    # PARAMETERS
    qs: list = [0.501, 0.7, 0.95, 0.99]
    cs: list = [3, 4, 6, 7, 8.0]
    cs2: list = [12.0, 18, 24, 30]
    cidrs: list = np.arange(20, 24, 1).tolist()
    cidrs2: list = np.arange(32, 39, 2).tolist()
    es: list = [120]
    decays: list = ['default']
    ts: list = [30]

    # COLUMNS
    q_col: list = []
    c_col: list = []
    c2_col: list = []
    cidr_col: list = []
    cidr2_col: list = []

    # COMBINE
    for q in qs:
        for _ in range(len(cs) * len(cidrs)):
            q_col.append(q)
    for c in cs:
        for _ in range(len(cidrs)):
            c_col.append(c)
    for c in cs2:
        for _ in range(len(cidrs)):
            c2_col.append(c)

    c_col: list = int(len(q_col)/len(c_col)) * c_col
    c2_col: list = int(len(q_col)/len(c2_col)) * c2_col
    cidr_col: list = int(len(q_col)/len(cidrs)) * cidrs
    cidr2_col: list = int(len(q_col)/len(cidrs2)) * cidrs2

    return pd.DataFrame({
        'q': q_col,
        'c4': c_col,
        'c6': c2_col,
        'cidr4': cidr_col,
        'cidr6': cidr2_col,
        'e': len(q_col) * es,
        't': len(q_col) * ts,
        'decay': len(q_col) * decays,
    })


def get_query_w_columns(
    query: str,
    params: str,
    table: str = 'max.mini_internet_parameter_study',
    study: str = 'mini_internet'
) -> Tuple[str, list]:
    '''
    reads the query from given file, inserts the given parameter string and extracts the columns

    Arguments
    ---------
    query (str): filename of query within queries directory
    params (str): the identifier of parametrization to query
    table (str): the table to query from
    study (str): the study to query (e.g., mini_internet)

    Returns
    -------
    query (str): the query to execute
    columns (list[str]): list of column names of query
    '''
    query_file = open(f'/home/bergmmax/WORK/masterthesis/pipeline/queries/{query}.sql', 'r')
    query: str = query_file.read()

    query: str = query.replace('PARAMTERIZATION', params)
    query: str = query.replace('DB_TABLE', table)
    query: str = query.replace('STUDY', study)

    columns: list = []
    splitted: list = query.split('SELECT')[1].split('FROM')[0].split(',')

    for split in splitted:
        if 'AS' in split:
            app: str = split.split('AS')[1]
            app: str = app.replace(' ', '')
            app: str = app.replace('\n', '')
            columns.append(app)
        else:
            split: str = split.replace(' ', '')
            split: str = split.replace('\n', '')
            columns.append(split)

    return query, columns
