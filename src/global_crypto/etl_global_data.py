from datetime import timezone
import datetime
import os
import pandas as pd
import psycopg2
import requests
import time
import sqlalchemy
from configparser import ConfigParser

import sys
sys.path.append('src/')
from global_crypto.sql_queries import * # overall_crypto_insert, overall_market_share_insert,overall_defi_share_insert
from db_credentials import retrieve_credentials

# Input Parameters
url = 'https://api.coingecko.com/api/v3/'
global_endpoint = 'global'
defi_endpoint = 'global/decentralized_finance_defi'
credential_file_path = 'src/config.ini'

def create_table(create_table_script,cur,conn):
    cur.execute(create_table_script)
    conn.commit()

def get_raw_total_market_cap(url, global_endpoint):
    """"
    Desc:
        - Gets the JSON for total market cap. This feeds 
    Args:
        - Input the main URL and endpoint desired
    Returns
        - The json where the raw data is found
    """
    response = requests.get(url + global_endpoint)
    global_crypto_json = response.json()
    return global_crypto_json

def get_market_cap_share(global_crypto_json):
    """"
    Desc
        - Gets market cap share across coins from the JSON earlier
    Args
        - The json returns in get_raw_total_market_cap
    Returns
        - the market cap share dataframe
    
    """
    market_cap_pct = pd.DataFrame(
        data=global_crypto_json['data']['market_cap_percentage'].values(),
        index=global_crypto_json['data']['market_cap_percentage'].keys(),
        columns=['market_cap_percentage']
    )

    market_cap_pct['ingestion_timestamp'] = pd.to_datetime(global_crypto_json['data']['updated_at'], 
                                     unit='s')
    market_cap_pct['ingestion_date'] = market_cap_pct['ingestion_timestamp'].dt.date
    market_cap_pct['ingestion_time'] = market_cap_pct['ingestion_timestamp'].dt.time
    market_cap_pct = market_cap_pct.reset_index().rename({'index':'coin'},axis=1)
    
    return market_cap_pct

def get_total_mc(global_crypto_json):
    """
    Desc:
        - Gets the total market cap of the crypto universe
    Args:
        - The global crypto json returned from the get_raw_total_market_cap func
    Returns:
        - the total market cap dataframe
    """

    # Store total crypto market cap statistics
    total_market_cap_stats = pd.DataFrame(
    
    data = {'active_cryptocurrencies': global_crypto_json['data']['active_cryptocurrencies'],
            'markets':global_crypto_json['data']['markets'],
            'total_market_cap_usd':global_crypto_json['data']['total_market_cap']['usd'],
            'timestamp': pd.to_datetime(global_crypto_json['data']['updated_at'], unit='s')},
    
    index=[pd.to_datetime(global_crypto_json['data']['updated_at'], unit='s').date()])
    
    total_market_cap_stats = total_market_cap_stats.rename({'timestamp':'ingestion_timestamp'},axis=1)    
    total_market_cap_stats['ingestion_date'] = total_market_cap_stats['ingestion_timestamp'].dt.date
    total_market_cap_stats['ingestion_time'] = total_market_cap_stats['ingestion_timestamp'].dt.time

    total_market_cap_stats = total_market_cap_stats.reset_index().drop('index',axis=1)
    
    return total_market_cap_stats

def get_defi_mc(url, defi_endpoint):
    """ 
    Desc:
        - Gets the total defi statistics
    Args:
        - Url and the specific endpoint for DeFi stats
    Returns:
        - DeFi statistics DataFrame
    """
    response = requests.get(url + defi_endpoint)
    global_defi_json = response.json()

    defi_df = (pd.DataFrame(global_defi_json).T.reset_index().drop('index',axis=1))
    defi_df['ingestion_timestamp'] = datetime.datetime.now(timezone.utc)
    defi_df['ingestion_date'] = defi_df['ingestion_timestamp'].dt.date
    defi_df['ingestion_time'] = defi_df['ingestion_timestamp'].dt.time
    defi_df = defi_df.astype({
        'defi_market_cap':'float64',
        'eth_market_cap':'float64',
        'defi_to_eth_ratio':'float64',
        'trading_volume_24h':'float64',
        'defi_dominance':'float64',
        'top_coin_defi_dominance':'float64'}).round(2)
    defi_df.round(3)
    
    return defi_df

def insert_market_cap_share(global_crypto_json, cur, conn):
    """ 
    Desc:
        - Inserts the ingested data and inserts into a SQL database
    Args:
        - The global crypto json taken from get_raw_total_market_cap(). 
        - The cursor and connection for Postgres
    """
    df = get_market_cap_share(global_crypto_json) 

    data_list = list(df[['coin',
                         'market_cap_percentage', 
                         'ingestion_timestamp',
                         'ingestion_date',
                         'ingestion_time']].values)
    
    for data_row in data_list:
        cur.execute(overall_market_share_insert, data_row)
        conn.commit()

def insert_total_mc(global_crypto_json, cur, conn):
    """
    Desc:
        - Inserts the ingested data and inserts into a SQL database
    Args:
        - The global crypto json taken from get_raw_total_market_cap(). 
        - The cursor and connection for Postgres
    """

    df = get_total_mc(global_crypto_json)

    data_list = list(df[['active_cryptocurrencies',
                         'markets',
                         'total_market_cap_usd',
                         'ingestion_timestamp',
                         'ingestion_date',
                         'ingestion_time']].values[0])

    cur.execute(overall_crypto_insert, data_list)
    conn.commit()

def insert_defi_share(cur, conn):
    """
    Desc:
        - Inserts the ingested data and inserts into a SQL database
    Args:
        - The cursor and connection for Postgres
    """
    df = get_defi_mc(url, defi_endpoint)
    data_list = list(df[['defi_dominance',
                         'defi_market_cap',
                         'defi_to_eth_ratio',
                         'eth_market_cap',
                         'top_coin_defi_dominance',
                         'top_coin_name',
                         'trading_volume_24h',
                         'ingestion_timestamp',
                         'ingestion_date',
                         'ingestion_time']].values[0])

    cur.execute(overall_defi_share_insert, data_list)
    conn.commit()

def global_crypto_main():
    """
    Desc:
        Establishes a database connection, processes song and log data, then
        closes the cursor and database connection.
    """
    host, db, user, password = retrieve_credentials(credential_file=credential_file_path)
    conn = psycopg2.connect(f"host={host} dbname={db} user={user} password={password}")
    cur = conn.cursor()

    global_crypto_json = get_raw_total_market_cap(url, global_endpoint)
    
    create_table(overall_crypto,cur,conn)
    create_table(overall_market_share,cur,conn)
    create_table(overall_defi_share,cur,conn)

    insert_market_cap_share(global_crypto_json, cur, conn)
    print('Market cap share inserted')
    insert_total_mc(global_crypto_json,cur,conn)
    print('Global Crypto Inserted')
    insert_defi_share(cur, conn)
    print('Defi share inserted')

    conn.close()