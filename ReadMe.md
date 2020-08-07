# Query Global sign API for Certs bought in the previous month

This is designed for a lambda function storing the file in the tmp folder then loading to s3

To use locally 

## requirments
* python3
* whitlisted ip

## Setting up the code
git clone .....
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt


## Run
export S3_BUCKET_NAME=""

export globalsign_username=""

export globalsign_password=""

python3 ssl.py





## Notes and links

mailto:support@globalsign.com

Doc: https://www.globalsign.com/en/repository/ssl-api-documentation-v4.4.pdf 
- 8.6 Get Certificate Orders
- 8.2.1 GetOrderByOrderID Request