# Table Creation
# Skipped raw data ingestion
cleaned_defillama_table = (
    """
    CREATE TABLE IF NOT EXISTS cleaned_defillama
        (
          id INT,
          name TEXT,
          symbol TEXT,
          native_chain TEXT,
          audits INT,
          audit_note TEXT,
          gecko_id TEXT,
          cmcId TEXT,
          category TEXT,
          chains TEXT[],
          slug TEXT,
          native_tvl NUMERIC,
          chainTvls JSON,
          change_1d NUMERIC,
          change_7d NUMERIC,
          staking NUMERIC,
          fdv NUMERIC,
          mcap NUMERIC,
          mcap_nativetvl NUMERIC,
          ingestion_time TIMESTAMP
        );
    """
)

total_tvl_table = (
    """
    CREATE TABLE IF NOT EXISTS total_tvl
        (
          date DATE,
          totalLiquidityUSD NUMERIC
        );
    """
)

protocol_data_table = (
    """
    CREATE TABLE IF NOT EXISTS protocol_data
        (
          id INT,
          name TEXT,
          symbol TEXT,
          native_chain TEXT,
          audits INT,
          audit_note TEXT,
          gecko_id TEXT,
          cmcId TEXT,
          category TEXT,
          native_tvl NUMERIC,
          mcap NUMERIC,
          mcap_nativetvl NUMERIC,
          ingestion_time TIMESTAMP,
          rank_mcap_native_chain INT,
          rank_tvl_native_chain INT,
          rank_mcap_cat INT,
          rank_tvl_cat INT,
          rank_mcap_tvl_native_chain INT,
          rank_mcap_tvl_cat INT
        );
    """
)

protocol_chain_specific_data_table = (
    """
    CREATE TABLE IF NOT EXISTS protocol_chain_specific_data
        (
          id INT,
          name TEXT,
          symbol TEXT,
          gecko_id TEXT,
          chains TEXT,
          ingestion_time TIMESTAMP,
          tvl_chain_specific NUMERIC,
          rank INT
        );
    """
)

native_chain_agg_table = (
    """
    CREATE TABLE IF NOT EXISTS native_chain_agg
        (
         native_chain TEXT,
         ingestion_time TIMESTAMP,
         mcap NUMERIC,
         native_tvl NUMERIC
        );
    """
)

category_agg_table = (
    """
    CREATE TABLE IF NOT EXISTS category_agg
        (
         category TEXT,
         ingestion_time TIMESTAMP,
         mcap NUMERIC,
         native_tvl NUMERIC
        );
    """
)

chain_specific_agg_table = (
    """
    CREATE TABLE IF NOT EXISTS chain_specific_agg
        (
         chains TEXT,
         ingestion_time TIMESTAMP,
         tvl_chain_specific NUMERIC
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
    
# Table Creation
# Skipped raw data ingestion
cleaned_defillama_insert = (
    """
    INSERT INTO cleaned_defillama
        (
          id,
          name,
          symbol,
          native_chain,
          audits,
          audit_note,
          gecko_id,
          cmcId,
          category,
          chains,
          slug,
          native_tvl,
          chainTvls,
          change_1d,
          change_7d,
          staking,
          fdv,
          mcap,
          mcap_nativetvl,
          ingestion_time
        )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
    """
)

total_tvl_insert = (
    """
    INSERT INTO total_tvl
        (
          date,
          totalLiquidityUSD
        )
    VALUES (%s,%s);
    """
)

protocol_data_insert = (
    """
    INSERT INTO protocol_data
        (
          id,
          name,
          symbol,
          native_chain,
          audits,
          audit_note,
          gecko_id,
          cmcId,
          category,
          native_tvl,
          mcap,
          mcap_nativetvl,
          ingestion_time,
          rank_mcap_native_chain,
          rank_tvl_native_chain,
          rank_mcap_cat,
          rank_tvl_cat,
          rank_mcap_tvl_native_chain,
          rank_mcap_tvl_cat
        )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, %s);
    """
)

protocol_chain_specific_data_insert = (
    """
    INSERT INTO protocol_chain_specific_data
        (
          id,
          name,
          symbol,
          gecko_id,
          chains,
          ingestion_time,
          tvl_chain_specific,
          rank
        )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s);
    """
)

native_chain_agg_insert = (
    """
    INSERT INTO native_chain_agg
        (
         native_chain,
         ingestion_time,
         mcap,
         native_tvl
        )
    VALUES (%s,%s,%s,%s);
    """
)

category_agg_insert = (
    """
    INSERT INTO category_agg
        (
         category,
         ingestion_time,
         mcap,
         native_tvl
        )
    VALUES (%s,%s,%s,%s);
    """
)

chain_specific_agg_insert = (
    """
    INSERT INTO chain_specific_agg
        (
         chains,
         ingestion_time,
         tvl_chain_specific
        )
    VALUES (%s,%s,%s);
    """
)

create_table_queries = [cleaned_defillama_table, total_tvl_table, protocol_data_table, protocol_chain_specific_data_table, native_chain_agg_table, category_agg_table, chain_specific_agg_table]