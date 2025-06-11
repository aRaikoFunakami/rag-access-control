from dotenv import load_dotenv

# 環境変数をロード
load_dotenv()

# ==== Google Drive API 関連 ====

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ==== LangChain + Chroma 関連 ====

from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import json


# ======= Google Drive 関数 =======

SCOPES = [
    'https://www.googleapis.com/auth/drive.metadata.readonly',
    'https://www.googleapis.com/auth/documents.readonly'
]

def get_credentials():
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    return creds

def get_drive_service(creds):
    return build('drive', 'v3', credentials=creds)

def get_docs_service(creds):
    return build('docs', 'v1', credentials=creds)

def get_document_text(file_id, docs_service):
    document = docs_service.documents().get(documentId=file_id).execute()
    content = document.get('body', {}).get('content', [])
    text = ''
    for element in content:
        paragraph = element.get('paragraph')
        if not paragraph:
            continue
        for el in paragraph.get('elements', []):
            text_run = el.get('textRun')
            if text_run:
                text += text_run.get('content', '')
    return text

def list_files_and_permissions(folder_id):
    creds = get_credentials()
    drive_service = get_drive_service(creds)
    docs_service = get_docs_service(creds)
    query = f"'{folder_id}' in parents and trashed = false"
    results = drive_service.files().list(q=query, fields="files(id, name, mimeType)").execute()
    files = results.get('files', [])

    data = []
    for file in files:
        permissions = drive_service.permissions().list(
            fileId=file['id'],
            fields="permissions(id,emailAddress,role,type)"
        ).execute()
        file_info = {
            "id": file['id'],
            "name": file['name'],
            "mimeType": file['mimeType'],
            "permissions": permissions.get('permissions', [])
        }
        if file['mimeType'] == 'application/vnd.google-apps.document':
            try:
                content = get_document_text(file['id'], docs_service)
                file_info["content"] = content
            except Exception as e:
                file_info["content"] = "(本文の取得に失敗しました)"
        data.append(file_info)

    return data

# ======= Embedding 関数 =======
def format_for_embedding(file_data):
    documents = []
    metadatas = []

    for file in file_data:
        # Google Docs の本文がある場合はそれを使用
        content_body = file.get("content", "")
        content = f"File: {file['name']}\nType: {file['mimeType']}\nContent:\n{content_body}"

        permissions_structured = []
        for perm in file['permissions']:
            permissions_structured.append({
                "type": perm.get("type"),
                "email": perm.get("emailAddress", "N/A"),
                "role": perm.get("role")
            })

        metadata = {
            "source": "google_drive",
            "file_id": file["id"],
            "file_name": file["name"],
            "mime_type": file["mimeType"],
            "permissions": json.dumps(permissions_structured, ensure_ascii=False)
        }

        documents.append(content)
        metadatas.append(metadata)

    return documents, metadatas

def embed_to_chroma(documents, metadatas, persist_directory=".chroma"):
    embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

    vectorstore = Chroma.from_texts(
        collection_name="default",
        texts=documents,
        embedding=embedding_model,
        metadatas=metadatas,
        persist_directory=persist_directory
    )
    vectorstore.persist()
    print(f"Embedding completed and stored to Chroma DB at '{persist_directory}'")

# ======= メイン処理 =======

def main():
    folder_id = input("Google Drive Folder ID を入力してください: ").strip()
    print("Google Driveからファイルとパーミッションを取得中...")
    file_data = list_files_and_permissions(folder_id)

    print("Embedding データを整形中...")
    documents, metadatas = format_for_embedding(file_data)

    print("Chroma に保存中...")
    embed_to_chroma(documents, metadatas)

if __name__ == "__main__":
    main()