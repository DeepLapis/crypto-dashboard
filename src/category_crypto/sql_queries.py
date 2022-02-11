# Table Creation

crypto_category = (
    """
    CREATE TABLE IF NOT EXISTS crypto_category
        (
          id TEXT,
          category TEXT,
          market_cap NUMERIC,
          num_tokens INT,
          volume NUMERIC,
          last_updated TIMESTAMP
        );
    """
)

# Data Insertion
crypto_category_insert = (
    """
    INSERT INTO crypto_category
        (
          id,
          category,
          market_cap,
          num_tokens,
          volume,
          last_updated
        )
    VALUES (%s, %s, %s, %s, %s, %s);
    """
)
    
# DROP TABLE
drop_crypto_category_table = "DROP TABLE IF EXISTS crypto_category"

create_table_queries = crypto_category
drop_table_queries = drop_crypto_category_table
