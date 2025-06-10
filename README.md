# UNIXライクなアクセス制御付きのRAG検索

## 0. はじめに

このサンプルコードでは、「UNIXライクなアクセス制御」をRAG（Retrieval-Augmented Generation）の「検索」部分に適用し、
「ユーザーごとにアクセスできる文書だけでRAGを成立させる」という仕組みをシンプル＆明快に実現しています。

### 使用方法

サンプルプログラムの利用方法

#### OPENAI_APY_KEY の設定

```terminal
export OPENAI_API_KEY=<YOUR_API_KEY>
echo $OPENAI_API_KEY
```

#### 実行

```terminal
git clone https://github.com/aRaikoFunakami/rag-access-control.git
cd rag-access-control/
uv venv
uv run main.py
```

## 1. RAGにおける「アクセス制御」の全体像

通常のRAG：
質問クエリをベクトル化し、全ドキュメント集合から意味的に近いものを検索→LLMに渡す

このサンプルのRAG：
検索の候補（類似文書）を「そのユーザーが読んでよい文書だけ」にフィルタリングする

## 2. UNIXライクなアクセス権の仕組み

各ドキュメントは次の3軸で「読み取り権限」を持ちます：

- owner（所有者）： そのユーザーだけ読める（例: r--の左側）
- group（グループ）： 所定グループ所属ユーザーが読める（例: -r-の中央）
- other（全体）： だれでも読める（例: --rの右端）

例："rr-"なら「owner・groupが読める」「その他は読めない」

## 3. ポイント

can_access() 関数で検索結果に「アクセス可能」か「否か」を判断する

```:python
def can_access(self, user: User, doc: Document) -> bool:
    if user.user_id == doc.owner:
        return doc.permissions.get('owner', False)
    elif doc.group in user.groups:
        return doc.permissions.get('group', False)
    else:
        return doc.permissions.get('other', False)
```

## 4. 結果：「RAGの範囲自体がユーザーごとに変化」

プログラムの実行

```terminal
uv run main.py
```

実行結果

```terminal: 実行結果
Anonymized telemetry enabled. See                     https://docs.trychroma.com/telemetry for more information.
Chroma collection 'acvdb_demo' initialized.
HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
▼【サンプル文書】
doc_id | title                   | owner    | group  | perm
doc1  | プロジェクト設計書              | alice    | eng    | r--
doc2  | API仕様書                 | bob      | eng    | rr-
doc3  | マーケ戦略                  | charlie  | mkt    | rr-
doc4  | リモートワークガイド             | admin    | all    | rrr
doc5  | 技術スタック標準化              | alice    | eng    | rr-

▼【サンプルユーザー】
alice   | groups: eng
bob     | groups: eng
charlie | groups: mkt
david   | groups: sales
guest   | groups: (none)

▼【アクセス権マトリクス（r=可）】
user/doc | doc1     | doc2     | doc3     | doc4     | doc5    
alice    | r        | r        | -        | r        | r       
bob      | -        | r        | -        | r        | r       
charlie  | -        | -        | r        | r        | -       
david    | -        | -        | -        | r        | -       
guest    | -        | -        | -        | r        | -       

------------------------------------------------------------
▼【検索デモ・アクセス制御ログ付き】

■テストケース1：「API」 by alice

[検索ログ] Query: 'API' User: alice
HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
《〇》[doc2] 'API仕様書' (owner:bob, group:eng, perm:rr-) ... 類似度: 0.6466
《〇》[doc5] '技術スタック標準化' (owner:alice, group:eng, perm:rr-) ... 類似度: 0.5320
《〇》[doc4] 'リモートワークガイド' (owner:admin, group:all, perm:rrr) ... 類似度: 0.5295
《〇》[doc1] 'プロジェクト設計書' (owner:alice, group:eng, perm:r--) ... 類似度: 0.4976
《×》[doc3] 'マーケ戦略' (owner:charlie, group:mkt, perm:rr-) ... 類似度: 0.4879
 → ヒット: [doc2] API仕様書 : APIの認証・エラー・レート制限 (類似度: 0.6466)

 → ヒット: [doc5] 技術スタック標準化 : Python/React/PostgreSQL (類似度: 0.5320)

 → ヒット: [doc4] リモートワークガイド : 全社員向けポリシー (類似度: 0.5295)


■テストケース2：「API」 by charlie

[検索ログ] Query: 'API' User: charlie
HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
《×》[doc2] 'API仕様書' (owner:bob, group:eng, perm:rr-) ... 類似度: 0.6466
《×》[doc5] '技術スタック標準化' (owner:alice, group:eng, perm:rr-) ... 類似度: 0.5320
《〇》[doc4] 'リモートワークガイド' (owner:admin, group:all, perm:rrr) ... 類似度: 0.5295
《×》[doc1] 'プロジェクト設計書' (owner:alice, group:eng, perm:r--) ... 類似度: 0.4976
《〇》[doc3] 'マーケ戦略' (owner:charlie, group:mkt, perm:rr-) ... 類似度: 0.4879
 → ヒット: [doc4] リモートワークガイド : 全社員向けポリシー (類似度: 0.5295)

 → ヒット: [doc3] マーケ戦略 : Q2の施策まとめ (類似度: 0.4879)


■テストケース3：「リモートワーク」 by guest

[検索ログ] Query: 'リモートワーク' User: guest
HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
《〇》[doc4] 'リモートワークガイド' (owner:admin, group:all, perm:rrr) ... 類似度: 0.7860
《×》[doc5] '技術スタック標準化' (owner:alice, group:eng, perm:rr-) ... 類似度: 0.6174
《×》[doc2] 'API仕様書' (owner:bob, group:eng, perm:rr-) ... 類似度: 0.6134
《×》[doc1] 'プロジェクト設計書' (owner:alice, group:eng, perm:r--) ... 類似度: 0.6097
《×》[doc3] 'マーケ戦略' (owner:charlie, group:mkt, perm:rr-) ... 類似度: 0.5840
 → ヒット: [doc4] リモートワークガイド : 全社員向けポリシー (類似度: 0.7860)


■テストケース4：「設計」 by alice

[検索ログ] Query: '設計' User: alice
HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
《〇》[doc1] 'プロジェクト設計書' (owner:alice, group:eng, perm:r--) ... 類似度: 0.6907
《〇》[doc2] 'API仕様書' (owner:bob, group:eng, perm:rr-) ... 類似度: 0.5904
《×》[doc3] 'マーケ戦略' (owner:charlie, group:mkt, perm:rr-) ... 類似度: 0.5875
《〇》[doc5] '技術スタック標準化' (owner:alice, group:eng, perm:rr-) ... 類似度: 0.5545
《〇》[doc4] 'リモートワークガイド' (owner:admin, group:all, perm:rrr) ... 類似度: 0.5502
 → ヒット: [doc1] プロジェクト設計書 : これは秘密の設計書です (類似度: 0.6907)

 → ヒット: [doc2] API仕様書 : APIの認証・エラー・レート制限 (類似度: 0.5904)

 → ヒット: [doc5] 技術スタック標準化 : Python/React/PostgreSQL (類似度: 0.5545)


■テストケース5：「設計」 by bob

[検索ログ] Query: '設計' User: bob
HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
《×》[doc1] 'プロジェクト設計書' (owner:alice, group:eng, perm:r--) ... 類似度: 0.6907
《〇》[doc2] 'API仕様書' (owner:bob, group:eng, perm:rr-) ... 類似度: 0.5904
《×》[doc3] 'マーケ戦略' (owner:charlie, group:mkt, perm:rr-) ... 類似度: 0.5875
《〇》[doc5] '技術スタック標準化' (owner:alice, group:eng, perm:rr-) ... 類似度: 0.5545
《〇》[doc4] 'リモートワークガイド' (owner:admin, group:all, perm:rrr) ... 類似度: 0.5502
 → ヒット: [doc2] API仕様書 : APIの認証・エラー・レート制限 (類似度: 0.5904)

 → ヒット: [doc5] 技術スタック標準化 : Python/React/PostgreSQL (類似度: 0.5545)

 → ヒット: [doc4] リモートワークガイド : 全社員向けポリシー (類似度: 0.5502)


■テストケース6：「技術」 by bob

[検索ログ] Query: '技術' User: bob
HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
《〇》[doc5] '技術スタック標準化' (owner:alice, group:eng, perm:rr-) ... 類似度: 0.6964
《×》[doc3] 'マーケ戦略' (owner:charlie, group:mkt, perm:rr-) ... 類似度: 0.6393
《×》[doc1] 'プロジェクト設計書' (owner:alice, group:eng, perm:r--) ... 類似度: 0.6298
《〇》[doc2] 'API仕様書' (owner:bob, group:eng, perm:rr-) ... 類似度: 0.6275
《〇》[doc4] 'リモートワークガイド' (owner:admin, group:all, perm:rrr) ... 類似度: 0.6086
 → ヒット: [doc5] 技術スタック標準化 : Python/React/PostgreSQL (類似度: 0.6964)

 → ヒット: [doc2] API仕様書 : APIの認証・エラー・レート制限 (類似度: 0.6275)

 → ヒット: [doc4] リモートワークガイド : 全社員向けポリシー (類似度: 0.6086)
 ```

