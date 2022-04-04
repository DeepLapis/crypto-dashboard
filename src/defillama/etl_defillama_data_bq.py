import time
import sqlalchemy
import requests
import psycopg2
import pandas as pd
import os
import numpy as np
import json
import datetime
from datetime import timezone
from google.cloud import bigquery

# import sys
# sys.path.append('src/')
#from defillama.sql_queries import * 
#from db_credentials import retrieve_credentials

# # Input Parameters
# credential_file_path = 'src/config.ini'

# Create helper functions ->  create tables -> ingest data -> Wrap the ingestion in each function for app.py to call

# Helper Functions
def json_df_defillama(defillama_link):
    response = requests.get(defillama_link)
    df = pd.DataFrame(json.loads(json.dumps(response.json())))
    return df

def top_per_native_chain_category(protocol_list,mode=None, native_tvl=False,mcap=False,mcap_nativetvl=False):

    list_of_columns = ['id', 
                       'name', 
                       'symbol', 
                       'native_chain', 
                       'category',
                       'mcap',
                       'native_tvl',
                       'gecko_id', 
                       'cmcId',
                       'mcap_nativetvl',
                       'ingestion_time']
    
    if native_tvl+mcap+mcap_nativetvl>1:
        print('One must be true')
    elif  native_tvl+mcap+mcap_nativetvl==0:
        print('All cannot be false')
    elif mode==None:
        print('Please Choose a mode')

    elif mcap==True:
        #sorting by both columns
        df = protocol_list.loc[:,list_of_columns]
        df = df.sort_values('mcap',ascending=False)

        #create counter column used for later columns names
        df['rank'] = (df
                      #.sort_values('mcap',ascending=True)
                      .groupby([f'{mode}'],as_index=False)
                      [['mcap']]
                      .rank(method='dense', ascending=False))

        # Rank and order
        df = df.sort_values([f'{mode}','mcap','rank'],ascending=False)
        
        # Remove unneccessary columns
        df = df.loc[:,['id','rank','ingestion_time']]

        return df

    elif native_tvl==True:
        df = protocol_list.loc[:,list_of_columns]
        df = df.sort_values('native_tvl',ascending=False)

        #create counter column used for later columns names
        df['rank'] = (df
                      #.sort_values('native_tvl',ascending=True)
                      .groupby([f'{mode}'],as_index=False)
                      [['native_tvl']]
                      .rank(method='dense',ascending=False))

        # Rank and order
        df = df.sort_values([f'{mode}','native_tvl','rank'],ascending=False)
        
        # Remove unneccessary columns
        df = df.loc[:,['id','rank','ingestion_time']]

        return df
    
    # Smaller mcap/tvl is better
    elif mcap_nativetvl==True:
        df = protocol_list.loc[:,list_of_columns]
        df = df.sort_values('mcap_nativetvl',ascending=True)

        #create counter column used for later columns names
        df['rank'] = (df
                      #.sort_values('mcap_nativetvl',ascending=False)
                      .groupby([f'{mode}'],as_index=False)
                      [['mcap_nativetvl']]
                      .rank(method='dense', ascending=True))

        # Rank and order
        df = df.sort_values([f'{mode}','mcap_nativetvl','rank'],ascending=True)

        # Remove unneccessary columns
        df = df.loc[:,['id','rank','ingestion_time']]

        return df
    
def top_per_chain(protocol_chain_tvl):
    
    #sorting by both columns
    df = protocol_chain_tvl.sort_values('tvl_chain_specific',ascending=False)

    #create counter column used for later columns names
    df['rank'] = (df
                  # .sort_values('tvl_chain_specific',ascending=True)
                  .groupby(['chains'],as_index=False)
                  [['tvl_chain_specific']]
                  .rank(method='dense', ascending=False))

    # Rank and order
    df = df.sort_values(['chains','tvl_chain_specific','rank'],ascending=False)

    return df

def raw_defillama():
    """
    Desc:
        Ingests the data from DefiLlama Protocol endpoint
    Returns:
        A DataFrame
    
    """
    df = json_df_defillama('https://api.llama.fi/protocols')
    df['ingestion_time'] = pd.Timestamp.now() 
    return df

def clean_defillama(raw_defillama_df):
    """
    Desc:
        Removes tokens with 0 market cap, 
        get relavent columns, 
        computes mcap/tvl ratio,
        rename chain to native_chain
        rename tvl to native_tvl to avoid confusion
    Args:
        A list or array of columns to be sliced
    Returns:
        Cleaned dataFrame
    """
    # Get ingestion time
    columns_list = ['id', 
                'name', 
                'symbol', 
                'chain', 
                'audits', 
                'audit_note', 
                'gecko_id', 
                'cmcId', 
                'category', 
                'chains', 
                'slug', 
                'tvl', 
                'chainTvls',
                'change_1d', 
                'change_7d', 
                'staking', 
                'fdv', 
                'mcap',
                'mcap_nativetvl',
                'ingestion_time']
        
    raw_defillama_df['mcap_nativetvl'] = raw_defillama_df['mcap'] / raw_defillama_df['tvl']
    raw_defillama_df = raw_defillama_df.loc[:,columns_list]
    #raw_defillama_df = raw_defillama_df[raw_defillama_df['mcap']>0]
    raw_defillama_df['mcap_nativetvl'] = raw_defillama_df['mcap_nativetvl'].replace(np.inf, np.nan)
    raw_defillama_df['audits'] = raw_defillama_df['audits'].fillna(value=np.nan)
    raw_defillama_df['audits'] = raw_defillama_df['audits'].replace(np.nan, 0)
    cleaned_df = raw_defillama_df.rename({'chain':'native_chain','tvl':'native_tvl'},axis=1)
    
    return cleaned_df

def total_tvl():
    df = json_df_defillama('https://api.llama.fi/charts')
    df['date'] = pd.to_datetime(df['date'],unit='s')
    return df
    
########################################################################################################

def protocol_data(clean_defillama_df):
    """
    Desc:
        Generates a denormalized table with protocol specific data only and their ranks
    Args:
        Input the cleaned defillama df
    Returns:
        protocol_data and the corresponding ranks
    """
    protocol_df = clean_defillama_df.loc[:,['id', 
                                            'name', 
                                            'symbol', 
                                            'native_chain', 
                                            'audits', 
                                            'audit_note',
                                            'gecko_id', 
                                            'cmcId', 
                                            'category', 
                                            'native_tvl',
                                            'mcap',
                                            'mcap_nativetvl', 
                                            'ingestion_time']]
    
    # Permutations
    # Mode, native_tvl, mcap, mcap_nativetvl, table_name
    rank_permutations = [('native_chain',False,True,False,'rank_mcap_native_chain'),
                         ('native_chain',True,False,False,'rank_tvl_native_chain'),
                         ('category',False,True,False,'rank_mcap_cat'),
                         ('category',True,False,False,'rank_tvl_cat'),
                         ('native_chain',False,False,True,'rank_mcap_tvl_native_chain'),
                         ('category',False,False,True,'rank_mcap_tvl_cat')]
    
    for permutation in rank_permutations:
        df = top_per_native_chain_category(protocol_df,
                                           mode=permutation[0],
                                           native_tvl=permutation[1],
                                           mcap=permutation[2],
                                           mcap_nativetvl=permutation[3])
        
        
        protocol_df = (protocol_df.merge(df,
                                         how='left',
                                         on=['id','ingestion_time'])
                                  .rename({'rank':f'{permutation[4]}'},axis=1))                                       
    return protocol_df

def protocol_chain_specific_data(clean_defillama_df):
    chain_specific_df = clean_defillama_df.loc[:,['id',
                                                  'name',
                                                  'symbol',
                                                  'gecko_id',
                                                  'chains',
                                                  'chainTvls',
                                                  'ingestion_time']]
    
    chain_specific_df = chain_specific_df.explode('chains')
    tvl_chain = chain_specific_df.loc[:,['id','name','chainTvls']]
    
    tvl_chain = (pd.concat([tvl_chain, 
                            tvl_chain['chainTvls']
                            .apply(pd.Series)], axis=1)
                            .drop('chainTvls', axis=1))
    

    
    tvl_chain = pd.melt(tvl_chain, 
                             id_vars=['id','name'],
                             value_vars=tvl_chain.drop(['id','name'],axis=1).columns,
                             var_name='chains',
                             value_name='tvl')

    tvl_chain = tvl_chain.dropna().drop_duplicates()
    tvl_chain = tvl_chain.rename({'tvl':'tvl_chain_specific'},axis=1)
    
    chain_specific_df = (chain_specific_df.drop('chainTvls',axis=1)
                                          .merge(tvl_chain, 
                                                 how='left',
                                                 on=['id','name','chains']))
    
    chain_specific_df = top_per_chain(chain_specific_df)
    return chain_specific_df
    
def native_chain_agg(protocol_data_df):
    """
    Desc
        Aggregates the total market cap and tvl of a native chain
    Args
        Takes in the df generated by protocol data df
    Returns
        Returns the list of top native chains by market cap and tvl
        Ranked by market cap
    """
    list_of_columns = ['id','native_chain','mcap','native_tvl','ingestion_time']
    agg = (protocol_data_df.loc[:,list_of_columns]
                           .drop_duplicates()
                           .groupby(['native_chain','ingestion_time'],as_index=False)
                           [['mcap','native_tvl']].sum()
                           .sort_values('mcap',ascending=False))
    return agg

def category_agg(protocol_data_df):
    """
    Desc
        Aggregates the total market cap and tvl of a category
    Args
        Takes in the df generated by protocol data df
    Returns
        Returns the list of top native chains by market cap and tvl
        Ranked by market cap
    """
    list_of_columns = ['id','category','mcap','native_tvl','ingestion_time']
    agg = (protocol_data_df.loc[:,list_of_columns]
                           .drop_duplicates()
                           .groupby(['category','ingestion_time'],as_index=False)
                           [['mcap','native_tvl']].sum()
                           .sort_values('mcap',ascending=False))
    return agg

def chain_specific_agg(protocol_chain_specific_data_df):
    """
    Desc
        Aggregates the total market cap and tvl of a chain
    Args
        Takes in the df generated by protocol_chain_specific_data
    Returns
        Returns the list of top chain by market cap and tvl
        Ranked by market cap
    """
    list_of_columns = ['id','chains','tvl_chain_specific','ingestion_time']
    agg = (protocol_chain_specific_data_df.loc[:,list_of_columns]
                                          .drop_duplicates()
                                          .groupby(['chains','ingestion_time'],as_index=False)
                                          [['tvl_chain_specific']].sum()
                                          .sort_values('tvl_chain_specific',ascending=False))

    return agg

def insert_clean_defillama(clean_df,client, project_id, bq_dataset):
    """" 
    Desc:
        Transform the raw defillama data into a clean data then inserting them
    Args:
        Pass in the cursonr and connection
    """
    table_id = table_id = f"{project_id}.{bq_dataset}.cleaned_defillama"
    # To make it suitable to inject into postgres
    clean_df['chainTvls'] = clean_df['chainTvls'].apply(json.dumps) 

    df = clean_df.loc[:,[ 'id' ,
                          'name' ,
                          'symbol' ,
                          'native_chain' ,
                          'audits' ,
                          'audit_note' ,
                          'gecko_id' ,
                          'cmcId' ,
                          'category' ,
                          'chains' ,
                          'slug' ,
                          'native_tvl' ,
                          'chainTvls' ,
                          'change_1d' ,
                          'change_7d' ,
                          'staking' ,
                          'fdv' ,
                          'mcap' ,
                          'mcap_nativetvl',
                          'ingestion_time']]

    df['id'] = df['id'].astype(int)
    df['audits'] = df['audits'].astype(int)
   

    job_config = bigquery.LoadJobConfig(
    
    schema=[
        bigquery.SchemaField("id", bigquery.enums.SqlTypeNames.INT64),
        bigquery.SchemaField("name", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("symbol", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("native_chain", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("audits", bigquery.enums.SqlTypeNames.INT64),
        bigquery.SchemaField("audit_note", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("gecko_id", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("cmcId", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("category", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("chains", "STRING", "REPEATED"),
        bigquery.SchemaField("slug", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("native_tvl", bigquery.enums.SqlTypeNames.FLOAT64),
        bigquery.SchemaField("chainTvls", "STRING", mode="NULLABLE"),
        # bigquery.SchemaField("chainTvls", bigquery.enums.SqlTypeNames.STRUCT),
        bigquery.SchemaField("change_1d", bigquery.enums.SqlTypeNames.FLOAT64),
        bigquery.SchemaField("change_7d", bigquery.enums.SqlTypeNames.FLOAT64),
        bigquery.SchemaField("staking", bigquery.enums.SqlTypeNames.FLOAT64),
        bigquery.SchemaField("fdv", bigquery.enums.SqlTypeNames.FLOAT64),
        bigquery.SchemaField("mcap", bigquery.enums.SqlTypeNames.FLOAT64),
        bigquery.SchemaField("mcap_nativetvl", bigquery.enums.SqlTypeNames.FLOAT64),
        bigquery.SchemaField("ingestion_time", bigquery.enums.SqlTypeNames.TIMESTAMP)
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

def insert_total_tvl(total_tvl_df,client, project_id, bq_dataset):
    """
    Takes in total tvl data and returns the latest data only
    """
    table_id = table_id = f"{project_id}.{bq_dataset}.total_tvl"
    df = total_tvl_df.loc[:,['date', 'totalLiquidityUSD']]

    job_config = bigquery.LoadJobConfig(
    
    schema=[
        bigquery.SchemaField("date", bigquery.enums.SqlTypeNames.DATE),
        bigquery.SchemaField("totalLiquidityUSD", bigquery.enums.SqlTypeNames.FLOAT64)
    ],
    
    # Let the full DF from defillama return and replace the table rather than appending
    write_disposition="WRITE_TRUNCATE")

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

def insert_protocol_data(protocol_df,client, project_id, bq_dataset):
    """ 
    Takes the clean df, drops nested columns, and returns a column with ranked data
    """
    table_id = table_id = f"{project_id}.{bq_dataset}.protocol_data"
    df = protocol_df.loc[:,[ 'id' ,
                             'name' ,
                             'symbol' ,
                             'native_chain' ,
                             'audits' ,
                             'audit_note' ,
                             'gecko_id' ,
                             'cmcId' ,
                             'category' ,
                             'native_tvl' ,
                             'mcap' ,
                             'mcap_nativetvl' ,
                             'ingestion_time' ,
                             'rank_mcap_native_chain' ,
                             'rank_tvl_native_chain' ,
                             'rank_mcap_cat' ,
                             'rank_tvl_cat' ,
                             'rank_mcap_tvl_native_chain' ,
                             'rank_mcap_tvl_cat' ]]

    df['id'] = df['id'].astype(int)
    df['audits'] = df['audits'].astype(int)

    job_config = bigquery.LoadJobConfig(
    
    schema=[
        bigquery.SchemaField("id", bigquery.enums.SqlTypeNames.INTEGER),
        bigquery.SchemaField("name", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("symbol", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("native_chain", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("audits", bigquery.enums.SqlTypeNames.INTEGER),
        bigquery.SchemaField("audit_note", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("gecko_id", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("cmcId", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("category", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("native_tvl", bigquery.enums.SqlTypeNames.FLOAT64),
        bigquery.SchemaField("mcap", bigquery.enums.SqlTypeNames.FLOAT64),
        bigquery.SchemaField("mcap_nativetvl", bigquery.enums.SqlTypeNames.FLOAT64),
        bigquery.SchemaField("ingestion_time", bigquery.enums.SqlTypeNames.TIMESTAMP),
        bigquery.SchemaField("rank_mcap_native_chain", bigquery.enums.SqlTypeNames.INTEGER),
        bigquery.SchemaField("rank_tvl_native_chain", bigquery.enums.SqlTypeNames.INTEGER),
        bigquery.SchemaField("rank_mcap_cat", bigquery.enums.SqlTypeNames.INTEGER),
        bigquery.SchemaField("rank_tvl_cat", bigquery.enums.SqlTypeNames.INTEGER),
        bigquery.SchemaField("rank_mcap_tvl_native_chain", bigquery.enums.SqlTypeNames.INTEGER),
        bigquery.SchemaField("rank_mcap_tvl_cat", bigquery.enums.SqlTypeNames.INTEGER)
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

def insert_protocol_chain_specific_data(protocol_chain_specific_df,client, project_id, bq_dataset):
    """ 
    Takes in the clean data and take the nested columns
    """
    table_id = table_id = f"{project_id}.{bq_dataset}.protocol_chain_specific_data"
    df = protocol_chain_specific_df.loc[:,['id' ,
                                          'name',
                                          'symbol',
                                          'gecko_id',
                                          'chains',
                                          'ingestion_time',
                                          'tvl_chain_specific',
                                          'rank']]

    df['id'] = df['id'].astype(int) 

    job_config = bigquery.LoadJobConfig(
    
    schema=[
        bigquery.SchemaField("id", bigquery.enums.SqlTypeNames.INTEGER),
        bigquery.SchemaField("name", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("symbol", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("gecko_id", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("chains", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("ingestion_time", bigquery.enums.SqlTypeNames.TIMESTAMP),
        bigquery.SchemaField("tvl_chain_specific", bigquery.enums.SqlTypeNames.FLOAT64),
        bigquery.SchemaField("rank", bigquery.enums.SqlTypeNames.INTEGER)
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

def insert_native_chain_agg(protocol_df,client, project_id, bq_dataset):
    """  
    Takes in protocol data and groups native_chain and aggregating the sum of
    mcap and tvl
    """
    table_id = table_id = f"{project_id}.{bq_dataset}.native_chain_agg"
    df = native_chain_agg(protocol_df)
    
    df = df.loc[:,['native_chain' ,
                   'ingestion_time' ,
                   'mcap' ,
                   'native_tvl' ]]

    job_config = bigquery.LoadJobConfig(
    
    schema=[
        bigquery.SchemaField("native_chain", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("ingestion_time", bigquery.enums.SqlTypeNames.TIMESTAMP),
        bigquery.SchemaField("mcap", bigquery.enums.SqlTypeNames.FLOAT64),
        bigquery.SchemaField("native_tvl", bigquery.enums.SqlTypeNames.FLOAT64)
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

def insert_category_agg(protocol_df,client, project_id, bq_dataset):
    """  
    Takes in protocol data and groups category and aggregating the sum of
    mcap and tvl
    """
    table_id = table_id = f"{project_id}.{bq_dataset}.category_agg"
    
    df = category_agg(protocol_df)
    df = df.loc[:,['category',
                  'ingestion_time',
                  'mcap',
                  'native_tvl']]
    
    job_config = bigquery.LoadJobConfig(
    
    schema=[
        bigquery.SchemaField("category", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("ingestion_time", bigquery.enums.SqlTypeNames.TIMESTAMP),
        bigquery.SchemaField("mcap", bigquery.enums.SqlTypeNames.FLOAT64),
        bigquery.SchemaField("native_tvl", bigquery.enums.SqlTypeNames.FLOAT64)
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
   
def insert_chain_specific_agg(protocol_chain_specific_df,client, project_id, bq_dataset):
    """  
    Takes in the protocol chain specific data and aggregates them based on chains by chain specific tvl
    """
    table_id = table_id = f"{project_id}.{bq_dataset}.chain_specific_agg"
    df = chain_specific_agg(protocol_chain_specific_df)
    df = df.loc[:,['chains' ,
                  'ingestion_time' ,
                  'tvl_chain_specific']]

    job_config = bigquery.LoadJobConfig(
    
    schema=[
        bigquery.SchemaField("chains", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("ingestion_time", bigquery.enums.SqlTypeNames.TIMESTAMP),
        bigquery.SchemaField("tvl_chain_specific", bigquery.enums.SqlTypeNames.FLOAT64)
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
    
def defillama_main(client, project_id, bq_dataset):
    """
    Desc:
        Establishes a database connection, processes DefiLlama data, then
        closes the cursor and database connection.
    """

    print(f'Start processing Defillama Table')
    
    # Ingest and transform the data
    print('Start DefiLlama ingestion and transformation')
    total_tvl_df = total_tvl()
    print('1.Downloaded total defi tvl')

    raw_df = raw_defillama()
    print('2.Downloaded raw defi llama')

    clean_df = clean_defillama(raw_df)
    print('3.Transformed raw to clean data for defi llama')

    protocol_df = protocol_data(clean_df)
    print('4.Transformed clean to normalized data for defi llama')

    protocol_chain_specific_df = protocol_chain_specific_data(clean_df)
    print('5.Transformed clean to normalized CHAIN data for defi llama')

    # Transform and insert
    insert_clean_defillama(clean_df, client, project_id, bq_dataset)
    print('6.Inserted clean defi llama df')

    insert_total_tvl(total_tvl_df, client, project_id, bq_dataset)
    print('7.Inserted total defi tvl')

    insert_protocol_data(protocol_df, client, project_id, bq_dataset)
    print('8.Inserted protocol data')

    insert_protocol_chain_specific_data(protocol_chain_specific_df, client, project_id, bq_dataset)
    print('9.Inserted protocol chain specific data')

    insert_native_chain_agg(protocol_df, client, project_id, bq_dataset)
    print('10.Inserted aggregated native chain data')

    insert_category_agg(protocol_df, client, project_id, bq_dataset)
    print('11.Inserted aggregated category data')

    insert_chain_specific_agg(protocol_chain_specific_df, client,project_id, bq_dataset)
    print('12.Inserted aggregated chain_specific data')


# client = bigquery.Client()
# defillama_main(client, project_id, bq_dataset)