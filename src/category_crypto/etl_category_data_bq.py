import os
import sys
path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(path)
sys.path.append('src/')
from db_credentials import retrieve_cmc_api_credentials

import pandas as pd
import psycopg2
from google.cloud import bigquery
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from requests import Session
import json

def get_category_data(cmc_api):
    """"
    Desc:
        - Gets the data for crypto category 
    Args:
        - Input the API URL 
    Returns
        - The crypto_category dataframe 
    """
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/categories'
    headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': cmc_api,
    }

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url) #, params=parameters
        data = json.loads(response.text)
        #print(data)
        category_data_raw = [(x['id'], x['name'], x['market_cap'], x['num_tokens'], x['volume'], x['last_updated']) for x in data['data']]
        df_full_categories = pd.DataFrame(category_data_raw, columns = ['id', 'category', 'market_cap', 'num_tokens', 'volume', 'last_updated'])
        #df_full_categories.to_csv("cmc_category_list.csv",  index = False)
        return df_full_categories
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)
    
def insert_category_data(df, client, project_id, bq_dataset):
    table_id = f"{project_id}.{bq_dataset}.crypto_category"
    """ 
    Desc:
        - Inserts the ingested data and inserts into a SQL database
    Args:
        - The global crypto json taken from get_raw_total_market_cap(). 
        - The cursor and connection for Postgres
    """
    df = df.loc[:,['id',
                   'category',
                   'market_cap', 
                   'num_tokens',
                   'volume',
                   'last_updated']]
    
    job_config = bigquery.LoadJobConfig(
    
    schema=[
        bigquery.SchemaField("id", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("category", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("market_cap", bigquery.enums.SqlTypeNames.FLOAT64),
        bigquery.SchemaField("num_tokens", bigquery.enums.SqlTypeNames.INT64),
        bigquery.SchemaField("volume", bigquery.enums.SqlTypeNames.FLOAT64),
        bigquery.SchemaField("last_updated", bigquery.enums.SqlTypeNames.STRING)
    ],
    write_disposition="WRITE_APPEND")

    # Make an API request.
    job = client.load_table_from_dataframe(
    df, table_id, job_config=job_config)  
    
    # Wait for the job to complete.
    job.result()  

    table = client.get_table(table_id)  # Make an API request.
    return print(
            "Loaded {} rows and {} columns to {}".format(
            table.num_rows, len(table.schema), table_id)
            )

def category_crypto_main(client, project_id, bq_dataset):
    cmc_api = retrieve_cmc_api_credentials()
    df = get_category_data(cmc_api)
    insert_category_data(df, client, project_id, bq_dataset)
    print('Crypto categorical data inserted')


# project_id =''
# bq_dataset='crypto_bq'

# # Input Parameters
# url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/categories'
# cmc_api = retrieve_cmc_api_credentials()

# client = bigquery.Client()
# category_crypto_main(url, client)