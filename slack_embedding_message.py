from slack_sdk import WebClient
from dotenv import load_dotenv
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import os

load_dotenv()
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
client = WebClient(token=SLACK_BOT_TOKEN)

def fetch_messages(channel_id, channel_type, limit=100):
    messages = client.conversations_history(channel=channel_id, limit=limit).get('messages', [])
    members = client.conversations_members(channel=channel_id).get('members', [])
    permitted_str = ",".join(members)

    results = []
    for m in messages:
        if not m.get("text"):
            continue
        results.append({
            "text": m["text"],
            "metadata": {
                "source": "slack",
                "channel_id": channel_id,
                "channel_type": channel_type,
                "permitted_user_ids": permitted_str,
                "posted_by": m.get("user", "unknown")
            }
        })
    return results

def embed_messages_from_all_joined_channels():
    print("チャンネル一覧を取得中...")
    channels_response = client.conversations_list(types="public_channel,private_channel")
    channels = channels_response.get("channels", [])

    embedding_model = OpenAIEmbeddings()
    vectorstore = Chroma(
        collection_name="default",
        embedding_function=embedding_model,
        persist_directory=".chroma"
    )

    total_embedded = 0
    for ch in channels:
        if not ch.get("is_member", False):
            continue  # Botが参加していないチャンネルはスキップ

        channel_id = ch["id"]
        channel_name = ch.get("name", "unknown")
        channel_type = "private" if ch.get("is_private", False) else "public"

        print(f"{channel_name} ({channel_id}) を処理中...")

        data = fetch_messages(channel_id, channel_type)
        if not data:
            print("  メッセージが存在しません")
            continue

        texts = [d["text"] for d in data]
        metadatas = [d["metadata"] for d in data]

        vectorstore.add_texts(texts=texts, metadatas=metadatas)
        print(f"  {len(texts)}件を埋め込みました")
        total_embedded += len(texts)

    print(f"合計 {total_embedded} 件のメッセージを Chroma に埋め込みました")

if __name__ == "__main__":
    embed_messages_from_all_joined_channels()