import sys

from clickhouse_driver import Client


client: Client = Client('localhost')

parametrization: str = sys.argv[1]
study: str = sys.argv[2]
tables: list = ['range__subnet', 'aggregate_netid_ingress__mv_bundles', 'netstability', 'netstability_2']

query: str = '''
    ALTER TABLE max.REPLACE1_mini_internet
    DELETE
    WHERE
        parameter_study_name=='REPLACE2'
        and parameter_study_type=='REPLACE3';
'''

for table in tables:
    queryTable: str = query
    queryTable: str = queryTable.replace('REPLACE1', table)
    queryTable: str = queryTable.replace('REPLACE2', parametrization)
    queryTable: str = queryTable.replace('REPLACE3', study)

    client.execute(queryTable)
