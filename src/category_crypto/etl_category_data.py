import pandas as pd
import psycopg2

import sys
sys.path.append('src/')
from src.category_crypto.sql_queries import crypto_category, crypto_category_insert
from src.db_credentials import retrieve_credentials, retrieve_cmc_api_credentials

from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from requests import Session
import json

# Input Parameters
url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/categories'
credential_file_path = 'src/config.ini'
cmc_api = retrieve_cmc_api_credentials(credential_file=credential_file_path)

def create_table(create_table_script,cur,conn):
    cur.execute(create_table_script)
    conn.commit()

def get_category_data(url):
    """"
    Desc:
        - Gets the data for crypto category 
    Args:
        - Input the API URL 
    Returns
        - The crypto_category dataframe 
    """

    url = url
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
    

def insert_category_data(cur, conn):
    """ 
    Desc:
        - Inserts the ingested data and inserts into a SQL database
    Args:
        - The global crypto json taken from get_raw_total_market_cap(). 
        - The cursor and connection for Postgres
    """
    df = get_category_data(url)
    data_list = list(df[['id',
                         'category',
                         'market_cap', 
                         'num_tokens',
                         'volume',
                         'last_updated']].values)
    
    for data_row in data_list:
        cur.execute(crypto_category_insert, data_row)
        conn.commit()

def category_crypto_main():
    """
    Desc:
        Establishes a database connection, processes song and log data, then
        closes the cursor and database connection.
    """
    host, db, user, password = retrieve_credentials(credential_file=credential_file_path)
    conn = psycopg2.connect(f"host={host} dbname={db} user={user} password={password}")
    cur = conn.cursor()

    create_table(crypto_category,cur,conn)

    insert_category_data(cur, conn)
    print('Crypto categorical data inserted')
    conn.close()
