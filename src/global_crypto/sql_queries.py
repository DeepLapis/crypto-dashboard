# Table Creation

overall_crypto = (
    """
    CREATE TABLE IF NOT EXISTS overall_crypto_table
        (
          active_cryptocurrencies INT,
          markets INT,
          total_market_cap_usd NUMERIC,
          ingestion_timestamp TIMESTAMP,
          ingestion_date DATE,
          ingestion_time TIME
        );
    """
)

overall_market_share = (
    """ 
    CREATE TABLE IF NOT EXISTS overall_market_share_table
        (
            coin TEXT,
            market_cap_percentage NUMERIC,
            ingestion_timestamp TIMESTAMP,
            ingestion_date DATE,
            ingestion_time TIME
        );
    """
)

overall_defi_share = (
    """
    CREATE TABLE IF NOT EXISTS overall_defi_share
        (
            defi_dominance NUMERIC,
            defi_market_cap NUMERIC,
            defi_to_eth_ratio NUMERIC,
            eth_market_cap NUMERIC,
            top_coin_defi_dominance NUMERIC,
            top_coin_name TEXT,
            trading_volume NUMERIC,
            ingestion_timestamp TIMESTAMP,
            ingestion_date DATE,
            ingestion_time TIME
        );
    """
)

# Data Insertion
overall_crypto_insert = (
    """
    INSERT INTO overall_crypto_table
        (
          active_cryptocurrencies,
          markets,
          total_market_cap_usd,
          ingestion_timestamp,
          ingestion_date,
          ingestion_time
        )
    VALUES (%s, %s, %s, %s, %s, %s);
    """
)
    
overall_market_share_insert = (
    """ 
    INSERT INTO overall_market_share_table
        (
            coin,
            market_cap_percentage,
            ingestion_timestamp,
            ingestion_date,
            ingestion_time
        )
    VALUES (%s, %s, %s, %s, %s);
    """
)
overall_defi_share_insert =  (
    """
    INSERT INTO overall_defi_share
        (
            defi_dominance,
            defi_market_cap,
            defi_to_eth_ratio,
            eth_market_cap,
            top_coin_defi_dominance,
            top_coin_name,
            trading_volume,
            ingestion_timestamp,
            ingestion_date,
            ingestion_time
        )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
)

create_table_queries = [overall_crypto, overall_market_share, overall_defi_share]
