import json
from fastapi import FastAPI
from pydantic import BaseModel
from mangum import Mangum
import boto3
from boto3.dynamodb.conditions import Key, Attr
from typing import Union

app = FastAPI()

dynamo_resource = boto3.resource("dynamodb")

print(list(dynamo_resource.tables.all()))

user_table = dynamo_resource.Table("ArxivUser")
paper_table = dynamo_resource.Table("ArxivPaper")


class UserModel(BaseModel):
    user_id: str
    username: Union[str, None] = None
    first_name: Union[str, None] = None
    last_name: Union[str, None] = None
    papers: Union[list, None] = []


class PaperModel(BaseModel):
    paper_id: str
    paper_summary: Union[str, None] = None
    paper_name: Union[str, None] = None
    arxiv_details: dict = {"pdf": "", "url": ""}
    user_id: str


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/hello")
def hello():
    return {"message": "All is well"}


@app.post("/api/add_user")
def create_user(User: UserModel):
    user = dict(user_id=User.user_id,
                username=User.username,
                first_name=User.first_name,
                last_name=User.last_name,
                papers=User.papers if User.papers else [])

    resp = user_table.put_item(Item=user)

    if resp["ResponseMetadata"]["HTTPStatusCode"] == 200:
        return {"ok": True}

    return {"ok": False}


@app.post("/api/add_paper")
def create_paper(Paper: PaperModel):
    arxiv_details = Paper.arxiv_details
    paper = dict(paper_id=Paper.paper_id,
                 paper_name=Paper.paper_name,
                 paper_summary=Paper.paper_summary,
                 arxiv_details=arxiv_details)
    print(f'PAPER: {paper}')
    paper_resp = paper_table.put_item(Item=paper)
    if paper_resp["ResponseMetadata"]["HTTPStatusCode"] != 200:
        return {"ok": False}
    # update user
    user_id = Paper.user_id
    update_resp = user_table.update_item(
        Key={"user_id": user_id},
        UpdateExpression="SET papers = list_append(papers, :paper_id)",
        ExpressionAttributeValues={":paper_id": [paper["paper_id"]]},
        ReturnValues="UPDATED_NEW")

    if update_resp["ResponseMetadata"]["HTTPStatusCode"] != 200:
        return {"ok": False}
    return {"ok": True}


lambda_handler = Mangum(app, lifespan="off")

# import requests

# def lambda_handler(event, context):
#     """Sample pure Lambda function

#     Parameters
#     ----------
#     event: dict, required
#         API Gateway Lambda Proxy Input Format

#         Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

#     context: object, required
#         Lambda Context runtime methods and attributes

#         Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

#     Returns
#     ------
#     API Gateway Lambda Proxy Output Format: dict

#         Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
#     """

#     # try:
#     #     ip = requests.get("http://checkip.amazonaws.com/")
#     # except requests.RequestException as e:
#     #     # Send some context about this error to Lambda Logs
#     #     print(e)

#     #     raise e

#     return {
#         "statusCode": 200,
#         "body": json.dumps({
#             "message": "hello world",
#             # "location": ip.text.replace("\n", "")
#         }),
#     }
