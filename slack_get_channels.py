# テスト用スクリプト
from slack_sdk import WebClient
import os
from dotenv import load_dotenv

load_dotenv()
client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])

response = client.conversations_list()
for channel in response["channels"]:
    print(f"{channel['name']} => {channel['id']}")