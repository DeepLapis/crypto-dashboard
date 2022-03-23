from datetime import timezone
import datetime
import pandas as pd
import requests
import time
from google.cloud import bigquery

# Input Parameters
url = 'https://api.coingecko.com/api/v3/'
global_endpoint = 'global'
defi_endpoint = 'global/decentralized_finance_defi'


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

def insert_market_cap_share(global_crypto_json,client, project_id, bq_dataset):
    """ 
    Desc:
        - Inserts the ingested data and inserts into a SQL database
    Args:
        - The global crypto json taken from get_raw_total_market_cap(). 
        - The cursor and connection for Postgres
    """
    table_id = f"{project_id}.{bq_dataset}.overall_crypto"
    df = get_market_cap_share(global_crypto_json) 

    df = df.loc[:,['coin',
                   'market_cap_percentage', 
                   'ingestion_timestamp',
                   'ingestion_date',
                   'ingestion_time']]
    
    job_config = bigquery.LoadJobConfig(
    
    schema=[
        bigquery.SchemaField("coin", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("market_cap_percentage", bigquery.enums.SqlTypeNames.FLOAT64),
        bigquery.SchemaField("ingestion_timestamp", bigquery.enums.SqlTypeNames.TIMESTAMP),
        bigquery.SchemaField("ingestion_date", bigquery.enums.SqlTypeNames.DATE),
        bigquery.SchemaField("ingestion_time", bigquery.enums.SqlTypeNames.TIME)
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

def insert_total_mc(global_crypto_json,client, project_id, bq_dataset):
    """
    Desc:
        - Inserts the ingested data and inserts into a SQL database
    Args:
        - The global crypto json taken from get_raw_total_market_cap(). 
        - The cursor and connection for Postgres
    """
    table_id = table_id = f"{project_id}.{bq_dataset}.overall_market_share_table"
    df = get_total_mc(global_crypto_json)
    df = df.loc[:,['active_cryptocurrencies',
                   'markets',
                   'total_market_cap_usd',
                   'ingestion_timestamp',
                   'ingestion_date',
                   'ingestion_time']]

    job_config = bigquery.LoadJobConfig(
    
    schema=[
        bigquery.SchemaField("active_cryptocurrencies", bigquery.enums.SqlTypeNames.INT64),
        bigquery.SchemaField("markets", bigquery.enums.SqlTypeNames.INT64),
        bigquery.SchemaField("total_market_cap_usd", bigquery.enums.SqlTypeNames.FLOAT64),
        bigquery.SchemaField("ingestion_timestamp", bigquery.enums.SqlTypeNames.TIMESTAMP),
        bigquery.SchemaField("ingestion_date", bigquery.enums.SqlTypeNames.DATE),
        bigquery.SchemaField("ingestion_time", bigquery.enums.SqlTypeNames.TIME)
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

def insert_defi_share(client, project_id, bq_dataset):
    table_id = table_id = f"{project_id}.{bq_dataset}.overall_defi_share"
    """
    Desc:
        - Inserts the ingested data and inserts into a SQL database
    Args:
        - The cursor and connection for Postgres
    """
    df = get_defi_mc(url, defi_endpoint)
    df = df.loc[:,['defi_dominance',
                   'defi_market_cap',
                   'defi_to_eth_ratio',
                   'eth_market_cap',
                   'top_coin_defi_dominance',
                   'top_coin_name',
                   'trading_volume_24h',
                   'ingestion_timestamp',
                   'ingestion_date',
                   'ingestion_time']]

    job_config = bigquery.LoadJobConfig(
    
    schema=[
        bigquery.SchemaField("defi_dominance", bigquery.enums.SqlTypeNames.FLOAT64),
        bigquery.SchemaField("defi_market_cap", bigquery.enums.SqlTypeNames.FLOAT64),
        bigquery.SchemaField("defi_to_eth_ratio", bigquery.enums.SqlTypeNames.FLOAT64),
        bigquery.SchemaField("eth_market_cap", bigquery.enums.SqlTypeNames.FLOAT64),
        bigquery.SchemaField("top_coin_defi_dominance", bigquery.enums.SqlTypeNames.FLOAT64),
        bigquery.SchemaField("top_coin_name", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("trading_volume_24h", bigquery.enums.SqlTypeNames.FLOAT64),
        bigquery.SchemaField("ingestion_timestamp", bigquery.enums.SqlTypeNames.TIMESTAMP),
        bigquery.SchemaField("ingestion_date", bigquery.enums.SqlTypeNames.DATE),
        bigquery.SchemaField("ingestion_time", bigquery.enums.SqlTypeNames.TIME)
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

def global_crypto_main(client, project_id, bq_dataset):
    global_crypto_json = get_raw_total_market_cap(url, global_endpoint)
    insert_market_cap_share(global_crypto_json, client, project_id, bq_dataset)
    print('Market cap share inserted')
    insert_total_mc(global_crypto_json, client, project_id, bq_dataset)
    print('Global Crypto Inserted')
    insert_defi_share(client, project_id, bq_dataset)  
    print('Defi share inserted')

# client = bigquery.Client()
# category_crypto_main(url, client)