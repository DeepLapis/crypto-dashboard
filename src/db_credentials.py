from configparser import ConfigParser
from google.cloud import secretmanager

def access_secret_version(PROJECT_ID, secret_id, version_id="latest"):
    # Create the Secret Manager client.
    client = secretmanager.SecretManagerServiceClient()
    # Build the resource name of the secret version.
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/{version_id}"
    # Access the secret version.
    response = client.access_secret_version(name=name)
    # Return the decoded payload.
    return response.payload.data.decode('UTF-8')

# def retrieve_credentials(credential_file=None):
#     credential_file = None
#     host=
#     # host=
#     db=
#     user=
#     password=

#     return host, db, user, password

def retrieve_cmc_api_credentials(credential_file=None):
    credential_file = None
    cmc_api=
    return cmc_api

# ######### FOR LOCAL DEVELOPMENT #########
# # Activate this if you are developing locally
# def retrieve_credentials(credential_file):
#     config = ConfigParser()
#     config.read(credential_file)
    
#     postgres_config = config["postgresql"]
#     host=postgres_config['host']
#     db=postgres_config['database']
#     user=postgres_config['user']
#     password=postgres_config['password']

#     return host, db, user, password

# def retrieve_cmc_api_credentials(credential_file):
#     config = ConfigParser()
#     config.read(credential_file)

#     postgres_config = config['cmc_api_key']
#     cmc_api=postgres_config['cmc_api']
#     # print(cmc_api)
#     return cmc_api