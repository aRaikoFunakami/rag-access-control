# show_documents.py
# 統一された表示プログラム（Google Drive, Slack, 今後の拡張も可能）

from langchain.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# ヘルパー関数

def format_permissions(perm_data):
    if isinstance(perm_data, list):
        return "\n".join(f"  - {p}" for p in perm_data)
    elif isinstance(perm_data, str):
        return f"  - {perm_data}"
    else:
        return "  - [Unknown format]"

# Chroma 初期化（共通コレクション）
embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma(
    collection_name="default",
    embedding_function=embedding_model,
    persist_directory=".chroma"
)

# ドキュメント取得（全件）
documents = vectorstore.similarity_search("", k=100)
print(f"Total documents: {len(documents)}\n")

# ドキュメントごとの表示
for i, doc in enumerate(documents):
    meta = doc.metadata
    source = meta.get("source", "unknown")

    print(f"--- Document {i + 1} ---")
    print(f"Source: {source}")

    if source == "slack":
        print(f"Text: {doc.page_content}")
        print("Metadata:")
        print(f"  - Channel: {meta.get('channel')} ({meta.get('channel_type')})")
        print(f"  - Posted By: {meta.get('posted_by')}")
        print(f"  - Permitted Users (Saved):")
        print(format_permissions(meta.get("permitted_users_saved")))
        print(f"  - Permitted Users (Latest):")
        print(format_permissions(meta.get("permitted_users_latest")))

    elif source == "google_drive":
        print(f"File Name: {meta.get('file_name')}")
        print(f"MIME Type: {meta.get('mime_type', 'unknown')}")
        print(f"File ID: {meta.get('file_id')}")
        print("Saved Permissions:")
        print(format_permissions(meta.get("permissions_saved")))
        print("Latest Permissions:")
        print(format_permissions(meta.get("permissions_latest")))
        print("\nSummary Text:")
        print(f"{doc.page_content}")

    else:
        print("[!] Unknown source or unsupported document type.")
        print(f"Content:\n{doc.page_content}")

    print("\n")