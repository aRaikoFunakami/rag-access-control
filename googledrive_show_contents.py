import os
import json
from dotenv import load_dotenv

from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ==== 環境変数ロード ====
load_dotenv()

# ==== Google Drive API 認証 ====
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']

def get_drive_service():
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    return build('drive', 'v3', credentials=creds)

# ==== Drive から最新の permission を取得 ====
def fetch_latest_permissions(service, file_id):
    try:
        permissions = service.permissions().list(
            fileId=file_id,
            fields="permissions(id,emailAddress,role,type)"
        ).execute()
        return permissions.get("permissions", [])
    except Exception as e:
        return [{"error": str(e)}]

# ==== permission 整形 ====
def format_permissions(permissions, title="Permissions"):
    if not permissions:
        return f"{title}: No permissions found"

    lines = [f"{title}:"]
    for p in permissions:
        if isinstance(p, dict) and "error" in p:
            lines.append(f"Error: {p['error']}")
        else:
            user_type = p.get("type", "unknown").capitalize()
            email = p.get("emailAddress", p.get("email", "N/A"))
            role = p.get("role", "N/A")
            lines.append(f"{user_type} — {email} → Role: {role}")
    return lines

# ==== Chroma からデータを取得して表示 ====
def display_chroma_documents(persist_directory=".chroma"):
    # Chroma 初期化
    embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma(
        collection_name="default",
        embedding_function=embedding_model,
        persist_directory=persist_directory
    )

    # Chroma からデータ取得
    results = vectorstore.get(include=["documents", "metadatas"])
    documents = results["documents"]
    metadatas = results["metadatas"]

    print(f"Total documents: {len(documents)}\n")

    # Google Drive 認証（初回のみブラウザ起動）
    print("Authenticating with Google Drive...")
    drive_service = get_drive_service()

    for i, (doc, meta) in enumerate(zip(documents, metadatas)):
        file_id = meta.get("file_id")
        print(f"\n--- Document {i + 1} ---")
        print(f"File Name: {meta.get('file_name')}")
        print(f"MIME Type: {meta.get('mime_type')}")
        print(f"File ID: {file_id}")

        # 保存された permissions（metadata）
        saved_perm_str = meta.get("permissions", "[]")
        try:
            saved_permissions = json.loads(saved_perm_str)
            print(format_permissions(saved_permissions, title="Saved Permissions in Metadata"))
        except json.JSONDecodeError:
            print("Invalid saved permissions format")

        # 最新の permissions（Google Drive）
        latest_permissions = fetch_latest_permissions(drive_service, file_id)
        print(format_permissions(latest_permissions, title="Latest Permissions from Google Drive"))

        # 任意で、ドキュメントの内容を表示
        print("\nSummary Text:")
        print(f"{doc}")

if __name__ == "__main__":
    display_chroma_documents()