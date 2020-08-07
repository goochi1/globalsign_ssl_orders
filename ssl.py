from zeep import Client, Settings
from zeep.wsse.username import UsernameToken
from zeep.plugins import HistoryPlugin
from datetime import date, timedelta
import json
import os
import boto3
import logging

logger = logging.getLogger()

# this script logs into global sign pulls in all ssl thats have been purchased for the prevoiuse month
# but you can hard code month in fmt commented out

def ssm_values(path):
    #if using in lambda store password in SSM to pass in 
    client = boto3.client("ssm")
    token = (
        client.get_parameter(
            Name=str(path), WithDecryption=True)
        .get("Parameter")
        .get("Value")
    )
    return token

def lambda_handler(event, context):
    CertOrders = []
    month,qmonth, year = date_range()
    username = os.environ["globalsign_username"]
    print(username)
    password = os.environ["globalsign_password"]

    
    # This is to get all the orders from last month
    get_certificate_orders_request_data = {
        "QueryRequestHeader": {
            "AuthToken": {"UserName": username, "Password": password}
        },
        "FromDate": f"{year}-{qmonth}-01T00:00:00.00Z",  #'2015-06-08T15:35:40.815Z',
        "ToDate": "",
        "FQDN": "",
        "ProductCode": "",
        "OrderStatus": "4",  # Issue completed
        "SubID": "",
    }
    OrderDetails = query_global_sign(
        get_certificate_orders_request_data, "GetCertificateOrders"
    )

    for item in OrderDetails:

        OrderID = item["OrderID"]

        get_order_by_id_request_data = {
            "QueryRequestHeader": {
                "AuthToken": {"UserName": username, "Password": password}
            },
            "OrderID": f"{OrderID}",
            "OrderQueryOption": {
                "OrderStatus": "",
                "ReturnOrderOption": "",
                "ReturnCertificateInfo": "",
                "ReturnFulfillment": "",
                "ReturnCACerts": "",
                "ReturnOriginalCSR": "",
                "ReturnPKCS12": "",
                "ReturnSANEntries": "",
            },
        }
        price = query_global_sign(get_order_by_id_request_data, "GetOrderByOrderID")

        item['Price'] = price
        item['Month'] = month
        item['Year'] = year
        CertOrders.append(item)

    write_file("orders", CertOrders)
    
    #exports to s3 if you would like
    #s3_upload("orders", month, year)
    

def query_global_sign(request_data, request):
    wsdl = "https://system.globalsign.com/kb/ws/v1/GASService?wsdl"
    history = HistoryPlugin()
    settings = Settings(strict=False)
    client = Client(wsdl, plugins=[history], settings=settings)

    try:
        if request == "GetCertificateOrders":
            response = client.service.GetCertificateOrders(request_data)
            print(response['QueryResponseHeader'])
            OrderDetails = response["SearchOrderDetails"]["SearchOrderDetail"]

        elif request == "GetOrderByOrderID":
            response = client.service.GetOrderByOrderID(request_data)
            OrderDetails = response['OrderDetail']['OrderInfo']['Price']

        return OrderDetails
    except Exception as e:
        logging.warning(f"{e}")


def date_range():

    prev = date.today().replace(day=1) - timedelta(days=1)
    month = prev.month
    year = prev.year
    if month < 10:
        qmonth = f"0{month}"

    return month, qmonth, year


def write_file(file_name, data):
    #if using in lambda put /tmp/ infront of file name here and in s3 part
    with open(f"{file_name}.json", "w") as outfile:
        for item in data:
            try:
                if item is None or len(item) == 0:
                    pass
                json.dump(item.__dict__["__values__"], outfile)

                outfile.write("\n")
            except Exception as e:
                logging.warning(f"{e}")
                pass

    logging.info("convtered to athena readable json")


def s3_upload(file_name, month, year):
    
    S3BucketName = os.environ["S3_BUCKET_NAME"]  
    s3 = boto3.resource("s3")
    s3.meta.client.upload_file(
        f"{file_name}.json",
        S3BucketName,
        f"GlobalSign/year={year}/month={month}/{file_name}-{year}-{month}.json",
    )
    logging.info("file uploaded")

#this is here to run locally but remove for lambda   
lambda_handler(None, None)