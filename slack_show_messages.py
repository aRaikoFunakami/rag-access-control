import os
from dotenv import load_dotenv
from slack_sdk import WebClient
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
client = WebClient(token=SLACK_BOT_TOKEN)

# キャッシュ用
user_cache = {}
channel_cache = {}

def get_user_name(user_id):
    if user_id in user_cache:
        return user_cache[user_id]
    try:
        info = client.users_info(user=user_id)
        name = info["user"]["real_name"]
        user_cache[user_id] = name
        return name
    except Exception:
        return user_id

def get_channel_name(channel_id):
    if channel_id in channel_cache:
        return channel_cache[channel_id]
    try:
        info = client.conversations_info(channel=channel_id)
        name = info["channel"]["name"]
        channel_cache[channel_id] = name
        return name
    except Exception:
        return channel_id

def get_latest_channel_members(channel_id):
    try:
        response = client.conversations_members(channel=channel_id)
        return [get_user_name(uid) for uid in response.get("members", [])]
    except Exception:
        return []

def display_embeddings():
    vectorstore = Chroma(
        collection_name="default",
        embedding_function=OpenAIEmbeddings(),
        persist_directory=".chroma"
    )

    print("Chroma に保存された Slack メッセージの埋め込み内容を確認します...")

    results = vectorstore.get(include=["documents", "metadatas"])
    documents = results["documents"]
    metadatas = results["metadatas"]

    for i, (doc, meta) in enumerate(zip(documents, metadatas), 1):
        channel_id = meta.get("channel_id", "N/A")
        channel_name = get_channel_name(channel_id)
        channel_type = meta.get("channel_type", "N/A")
        posted_by = get_user_name(meta.get("posted_by", "N/A"))
        permitted_raw = meta.get("permitted_user_ids", "")
        permitted_list = permitted_raw.split(",") if permitted_raw else []
        permitted_names = [get_user_name(uid) for uid in permitted_list]
        latest_members = get_latest_channel_members(channel_id)

        print(f"--- Slack Document {i} ---")
        print(f"Text: {doc}")
        print(f"Metadata:")
        print(f"  - Channel: {channel_name} ({channel_id})")
        print(f"  - Channel Type: {channel_type}")
        print(f"  - Posted By: {posted_by}")
        print(f"  - Permitted Users (Saved): {', '.join(permitted_names)}")
        print(f"  - Permitted Users (Latest): {', '.join(latest_members)}\n")

if __name__ == "__main__":
    display_embeddings()