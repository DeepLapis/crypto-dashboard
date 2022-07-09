# This would contain all the imports from the individual scripts that is 
# for pulling the data

# Our scripts will be stored in the source folder
from json import JSONDecodeError
import time
import sys
import os
sys.path.append('src/')
from src.global_crypto.etl_global_data_bq import global_crypto_main
from src.category_crypto.etl_category_data_bq import category_crypto_main
from src.defillama.etl_defillama_data_bq import defillama_main
from google.cloud import bigquery

## For CLoud SQL or PostGresVM
# from src.global_crypto.etl_global_data import global_crypto_main
# from src.category_crypto.etl_category_data import category_crypto_main
# from src.defillama.etl_defillama_data import defillama_main
from flask import Flask, Response
import requests

# For BQ
# # Turn on this section for Cloud SQL or Postgres VM
app = Flask(__name__)
@app.route("/")
def main():
    project_id =''
    bq_dataset=''
    client = bigquery.Client()
    try:
        # print("Testing coingecko ping")
        # gecko_ping = requests.get('https://api.coingecko.com/api/v3/ping')
        # print(gecko_ping.json()['gecko_says'])
        # print('Coingecko is ok')

        print('Ingesting global crypto data')
        global_crypto_main(client, project_id, bq_dataset)
        print('Successfully ingested global crypto data')

        print('Ingesting category data')
        category_crypto_main(client, project_id, bq_dataset)
        print('Successfully category data')

        print('Ingesting DefiLlama data')
        defillama_main(client, project_id, bq_dataset)
        print('Successfully ingested Defillama Data!')

    except Exception as e:
        print('Something has failed, ensuring atomicity. Good bye')
        # to intentially break the code for Cloud Scheduler to retry
        var1 = var2

    return ('Done',200)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0',port=int(os.environ.get("PORT",8080)))

# # Turn on this section for Cloud SQL or Postgres VM
# app = Flask(__name__)
# @app.route("/")
# def main():
#     try:
#         print("Testing coingecko ping")
#         gecko_ping = requests.get('https://api.coingecko.com/api/v3/ping')
#         print(gecko_ping.json()['gecko_says'])
#         print('Coingecko is ok')

#         print('Ingesting global crypto data')
#         global_crypto_main()
#         print('Successfully ingested global crypto data')

#         print('Ingesting category data')
#         category_crypto_main()
#         print('Successfully category data')

#         print('Ingesting DefiLlama data')
#         defillama_main()
#         print('Successfully ingested Defillama Data!')

#     except Exception as e:
#         print('Something has failed, ensuring atomicity. Good bye')
#         # to intentially break the code for Cloud Scheduler to retry
#         var1 = var2

#     return ('Done',200)

# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0',port=int(os.environ.get("PORT",8080)))


# ## For Local development
# def main():
   
#     # Test if coingecko is working
#     try:
#         gecko_ping = requests.get('https://api.coingecko.com/api/v3/ping')
#         print(gecko_ping.json()['gecko_says'])
#     except Exception as e:
#         print(str(e))
#         print('Coingecko is down')
    
#     # Get global crypto data
#     try:
#         global_crypto_main()
#     except Exception as e:
#         print(str(e))
#         print('Something wrong with global data coingecko')
#     # except JSONDecodeError as je:
#         print("global data failed")
#         # print('JSONDecodeError, coingecko down')
#         pass  

#     # Get Cateogry Data
#     try:
#         category_crypto_main()
#     # except JSONDecodeError as je:
#     except Exception as e:
#         print(str(e))
#         print('Something wrong with category data CMC')
#         # print('JSONDecodeError, CMC down')

#     # Get Defi Llama Data
#     try:
#         defillama_main()
#     # except JSONDecodeError as je:
#     except Exception as e:
#         print(str(e))
#         print('Something wrong with Defillama')
#         # print('JSONDecodeError, CMC down')
    
# if __name__ == '__main__':
#     main()


