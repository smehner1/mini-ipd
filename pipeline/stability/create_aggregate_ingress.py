from clickhouse_driver import Client
from datetime import datetime
from tqdm import tqdm
import pandas
import sys

client = Client('localhost')
parametrization = sys.argv[1]
study_type = sys.argv[2]

for cur_slice in range(8):

    query_file = open(f'queries/aggregate_ingress.sql', 'r')
    query: str = query_file.read()

    query: str = query.replace('REPLACEMENT3', study_type)
    query: str = query.replace('REPLACEMENT2', parametrization)
    query: str = query.replace('REPLACEMENT', str(cur_slice))

    progress = client.execute_with_progress(query)

    timeout: int = 3600
    started_at: datetime = datetime.now()

    for num_rows, total_rows in tqdm(progress, desc="import slice {}".format(cur_slice), ncols=20):
        pass
