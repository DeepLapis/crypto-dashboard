# Welcome To Crypto Dashboard

In this project, we would experimenting with building data pipeline, exploring the Crypto data ecosystem, and practicing some analytics skills.

# Folder Organization

The main working files are found in `working_directory`. This is the current status of the folders

```
crypto-dashboard
|___ data
|    |___ raw
|    |___ transform
|    |___ report
|
|___ notebooks
|
|___ src
|    |___ defillama
|         |___ etl_defillama_data.py
|         |___ sql_queries.py
|                    
|    |___ global_crypto
|         |___ etl_global_data.py
|         |___ sql_queries.py
|
|    |___ category_crypto
|         |___ etl_category_data.py
|         |___ sql_queries.py
|
|    |___ db_credentials.pu
|    |___ config.ini
|
|___ .env
|___ .gitignore
|___ .dockerignore
|___ app.py
|___ docker-compose.yml
|___ Dockerfile
|___ requirements.txt

Not even updated
```
Let's try to keep it neat so it would be easier to retrieve files

# Dependency management 
Before update `requirements.txt`:
1. git pull 
2. Install all new dependencies: `pip install -r requirements.txt `
3. Update ur newly installed dependencies to the list: `pip freeze > requirements.txt`  

# How to run the script
1) Check that you have the valid credentials in the crypto-dashboard directory. It should be at the same level as app.py. If you do not have this file, request from the author

2) Be in the same directory as `app.py`

3) In your terminal/PowerShell, run `docker compose up`

4) In another terminal in the same directory as `app.py`, run `python3 app.py`

As category data and global data do not have historical records, forward filling is required. `app.py` has a timer in a while loop that ingests data every `x` seconds that you set. Keep the script on and it will ingest data. Forward filling is where you ingest data forwards in time. 

# Setting Up Cloud Run
## Local Set up
### DockerFile
Ensure that you copy the scripts into the Docker container with the same directory structure. This is to allow the codes to function because they calling scripts and functions across different folders. Achieve this by writing a DockerFile provided

Check that `CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app ` is correct. In this case, the first app in `app:app` is the NAME of the script where you intended function to run resides. The second app is the name of the flask application you called inside the `app` script. 

If you script is called main.py for example, then it will be written as `main:app`

Also, check the codes for the DockerFile, ensure you have the relevant files available i.e requirements_prod. You can generate this file yourself by filtering your own `requirements.txt` to reduce the size of the Docker Image

### db_credentials.py
This is the tricky park and there are 3 scenarios 

#### 1) Running locally with a local postgres
In this case, use the block that has `config['xxx']`. This pulls credentials from a local file. This connects the codes to a local postgres server that is started. This would require the use of an active docker compose started with `docker compose up`. 

#### 2) Running locally with Cloud SQL
In this case, use the function that has as credential_file is `None` (so as to avoid changes in the ETL scripts). In this case, type in the relevant details. The `HOST` should be the public IP address of the SQL DB. You can type the raw cmc api key

#### 3) Running in cloud with Cloud SQL
The settings remains as above with 2 exceptions. At this point, your password should be linked to the secret manager with the relevent project id and secret id. Then the `host` should be the connection url to the database

The CMC API key would also be invoked via the secret manager

`Note that in the event that connecting via Cloud SQL's IP, connection URL, and secret fails. It is likely that this is a permissions issue, or you have not set up the secret, or you are not logged into the gloud locally. Do it via gcloud init`

### App.py
There is nothing much to do except that if you want to test locally, remove:
```
app=Flask(__name__)
@app.route("/")
app.run(debug=True, host='<host IP>',port=int(os.environ.get("PORT",8080)))
```
If you are lazy to do so, then you can test the script by going to your browser typing `https://127.0.0.1:5000`. This would trigger the flask app which then in turns trigger the script. This method is not recommended because you can't really see the logs.

Instead, remove that three lines above while adding a `main()` under the `if __name__ == '__main__' `

## Pushing to Cloud
Once you have prepared the files above, head over to your CLI (after logging into your gcloud account) 
```
gcloud builds submit --tag gcr.io/crypto-dashboard-344307/<name_of_image>
gcloud run deploy --image gcr.io/crypto-dashboard-344307/<name_of_image> --platform managed
```

The first line would build the image and name the image (aka tag the image) while the second line would push the image and creates the cloud run instance. If it fails to work then there is a chance where the repo in the Google account to hold the containers is not created. Proceed to create it. 

You will meet some settings like naming the service, location, allow unauthorized invocations. This would be changed in GCP later.

Head on over to container and artifact registry to check if the images are sent there. Go on the Cloud Run to see if the push is successful.

## Cloud Run
In Cloud Run, here is where do some extra settings. Click on your Cloud Run instance and go to `edit and deploy new revision`

### Container Tab
1) Check that the container port is 8080 or one that matches your docker image (gunicorn) or the flask app.

2) CPU is only allocated during request processing

3) Memory 4GB, vCPU 2

4) Request time out: 1000 seconds

### Connetions
Cloud SQL connections -> Add Connection -> Choose the Cloud SQL db

### Security
Compute engine default

Done!

## Cloud Scheduler
Scripts in cloud run are invoked by visiting the url that looks like this `https://<container name>-hxz3jlrdla-as.a.run.app`. Cloud Scheduler will visit this link at the relevent timing to trigger the script

1) Head on over to Cloud Scheduler and schedule a job

2) Name the schedule, choose the appropriate region, frequency, and timezone

3) Target Type:HTTP, URL: copy and paste the link by your cloud run. It looks like `https://<container name>-hxz3jlrdla-as.a.run.app`. HTTP method: GET. Auth header -> Add OIDC token. Service account compute engine default

4) 5 Max Retry, max retry duration 0s, min back off: 65 seconds (for Coingecko API to reset after a min). Just leave max backoff and doublings alone.

5) Create

## Checks
Head over to cloud run and check the logs that the messages that needs to be printed is printed. 

If you would like to see that is going on in Cloud SQL, use `docke compose up` to spin up pgadmin and connect to Cloud SQL.
