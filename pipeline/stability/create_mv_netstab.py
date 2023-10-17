from clickhouse_driver import Client
from tqdm import tqdm
import sys

parametrization: str = sys.argv[1]
study_type: str = sys.argv[2]
client: Client = Client('localhost')
num_slices: int = 3

failures = []

# run query in slices and insert in netstability_2
for cur_slice in range(0, num_slices):
    query_file = open(f'queries/netstability.sql', 'r')
    query: str = query_file.read()
    query: str = query.replace('REPLACE1', str(num_slices))
    query: str = query.replace('REPLACE2', str(cur_slice))
    query: str = query.replace('REPLACE3', parametrization)
    query: str = query.replace('REPLACE4', study_type)

    try:
        progress = client.execute_with_progress(query)
        # client.execute(query)
        for num_rows, total_rows in tqdm(progress, desc=f"import slice {cur_slice}", ncols=20):
            pass
    except Exception as e:
        print(f"ERROR import failed: {parametrization}")
        # print(e)
        exit(0)
        failures.append(parametrization)

# print(failures)
exit(1)
