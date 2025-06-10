import os
import logging
from typing import List, Set, Dict
from dataclasses import dataclass, field
from dotenv import load_dotenv
import chromadb
from langchain_openai import OpenAIEmbeddings

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

@dataclass
class User:
    user_id: str
    groups: Set[str]

@dataclass
class Document:
    doc_id: str
    title: str
    content: str
    owner: str
    group: str
    permissions: Dict[str, bool]  # {'owner': bool, 'group': bool, 'other': bool}

class AccessControlledVectorDB:
    def __init__(self, collection_name="acvdb_demo"):
        self.documents: List[Document] = []
        self.collection_name = collection_name
        self.embeddings = OpenAIEmbeddings(openai_api_key=os.environ["OPENAI_API_KEY"])
        self.chroma_client = chromadb.Client()
        try:
            self.chroma_client.delete_collection(collection_name)
        except:
            pass
        self.collection = self.chroma_client.create_collection(collection_name)
        logger.info(f"Chroma collection '{collection_name}' initialized.")

    def _perm_str(self, doc: Document):
        p = doc.permissions
        return ''.join([
            'r' if p.get('owner', False) else '-',
            'r' if p.get('group', False) else '-',
            'r' if p.get('other', False) else '-',
        ])

    def add_document(self, doc: Document):
        self.documents.append(doc)
        meta = {
            "doc_id": doc.doc_id,
            "owner": doc.owner,
            "group": doc.group,
            "permissions": self._perm_str(doc)
        }
        text = f"{doc.title}\n{doc.content}"
        embedding = self.embeddings.embed_query(text)
        self.collection.add(
            embeddings=[embedding],
            documents=[text],
            metadatas=[meta],
            ids=[doc.doc_id]
        )

    def can_access(self, user: User, doc: Document) -> bool:
        if user.user_id == doc.owner:
            return doc.permissions.get('owner', False)
        elif doc.group in user.groups:
            return doc.permissions.get('group', False)
        else:
            return doc.permissions.get('other', False)

    def _perm_str(self, doc: Document):
        p = doc.permissions
        return ''.join([
            'r' if p.get('owner', False) else '-',
            'r' if p.get('group', False) else '-',
            'r' if p.get('other', False) else '-',
        ])

    def search(self, query: str, user: User, top_k: int = 3) -> List[Dict]:
        """RAG検索＋アクセス可否をログで出す"""
        logger.info(f"\n[検索ログ] Query: '{query}' User: {user.user_id}")
        query_embedding = self.embeddings.embed_query(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k * 4  # フィルタで減る可能性を考慮
        )
        hits = []
        for doc_text, meta, dist in zip(
            results["documents"][0], results["metadatas"][0], results["distances"][0]
        ):
            doc_obj = next(d for d in self.documents if d.doc_id == meta["doc_id"])
            can = self.can_access(user, doc_obj)
            logger.info(
                f"《{'〇' if can else '×'}》[{doc_obj.doc_id}] '{doc_obj.title}'"
                f" (owner:{doc_obj.owner}, group:{doc_obj.group}, perm:{self._perm_str(doc_obj)})"
                f" ... 類似度: {1-dist:.4f}"
            )
            if can:
                hits.append({
                    "doc_id": doc_obj.doc_id,
                    "title": doc_obj.title,
                    "content": doc_obj.content,
                    "similarity": 1-dist
                })
        return hits[:top_k]

def create_sample_data():
    docs = [
        Document("doc1", "プロジェクト設計書", "これは秘密の設計書です", "alice", "eng", {'owner': True, 'group': False, 'other': False}),
        Document("doc2", "API仕様書", "APIの認証・エラー・レート制限", "bob", "eng", {'owner': True, 'group': True, 'other': False}),
        Document("doc3", "マーケ戦略", "Q2の施策まとめ", "charlie", "mkt", {'owner': True, 'group': True, 'other': False}),
        Document("doc4", "リモートワークガイド", "全社員向けポリシー", "admin", "all", {'owner': True, 'group': True, 'other': True}),
        Document("doc5", "技術スタック標準化", "Python/React/PostgreSQL", "alice", "eng", {'owner': True, 'group': True, 'other': False}),
    ]
    users = [
        User("alice", {"eng"}),
        User("bob", {"eng"}),
        User("charlie", {"mkt"}),
        User("david", {"sales"}),
        User("guest", set()),
    ]
    return docs, users

def show_sample_data(docs, users, db):
    print("▼【サンプル文書】")
    print("doc_id | title                   | owner    | group  | perm")
    for d in docs:
        print(f"{d.doc_id:5} | {d.title:22} | {d.owner:8} | {d.group:6} | {db._perm_str(d)}")
    print("\n▼【サンプルユーザー】")
    for u in users:
        print(f"{u.user_id:7} | groups: {', '.join(u.groups) if u.groups else '(none)'}")
    print("\n▼【アクセス権マトリクス（r=可）】")
    header = ["user/doc"] + [d.doc_id for d in docs]
    print(" | ".join(f"{h:8}" for h in header))
    for u in users:
        line = [u.user_id]
        for d in docs:
            mark = "r" if db.can_access(u, d) else "-"
            line.append(mark)
        print(" | ".join(f"{x:8}" for x in line))
    print("\n" + "-" * 60)

def main():
    db = AccessControlledVectorDB()
    docs, users = create_sample_data()
    for doc in docs:
        db.add_document(doc)
    show_sample_data(docs, users, db)
    test_cases = [
        ("API", "alice"),    # engグループ、API仕様書(group:r)、可
        ("API", "charlie"),  # mktのみ、API仕様書(group:x)、不可
        ("リモートワーク", "guest"), # 全体公開ドキュメントのみ可
        ("設計", "alice"),   # 自分の秘密設計書 可
        ("設計", "bob"),     # 他人の秘密設計書 不可
        ("技術", "bob"),     # engグループなので可
    ]
    print("▼【検索デモ・アクセス制御ログ付き】")
    for i, (query, user_id) in enumerate(test_cases, 1):
        print(f"\n■テストケース{i}：「{query}」 by {user_id}")
        user = next(u for u in users if u.user_id == user_id)
        results = db.search(query, user)
        if not results:
            print(" → アクセス可能な一致文書はありません\n")
        else:
            for r in results:
                print(f" → ヒット: [{r['doc_id']}] {r['title']} : {r['content']} (類似度: {r['similarity']:.4f})\n")

if __name__ == "__main__":
    main()