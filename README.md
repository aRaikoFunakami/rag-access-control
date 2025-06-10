# UNIXライクなアクセス制御付き RAGの検索フェーズの制御

## 0. はじめに

このサンプルコードでは、「UNIXライクなアクセス制御」をRAG（Retrieval-Augmented Generation）の「検索」部分に適用し、
「ユーザーごとにアクセスできる文書だけでRAGを成立させる」という仕組みをシンプル＆明快に実現しています。

### 使用方法

サンプルプログラムの利用方法

#### OPENAI_API_KEY の設定

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
類似度検索で得られた文書候補の中から、「そのユーザーが閲覧可能な文書のみ」を抽出し、RAGに利用する

## 2. UNIXライクなアクセス権の仕組み

各ドキュメントは次の3軸で「読み取り権限」を持ちます：

- owner（所有者）： そのユーザーだけ読める（例: r--の左側）
- group（グループ）： 所定グループ所属ユーザーが読める（例: -r-の中央）
- other（全体）： だれでも読める（例: --rの右端）

例："rr-"なら「owner・groupが読める」「その他は読めない」

## 3. ポイント

類似度検索で得られた文書に対して、can_access() 関数を使ってアクセス権を評価し、ユーザーが閲覧可能なものだけを結果に含めます。

```:python
def can_access(self, user: User, doc: Document) -> bool:
    if user.user_id == doc.owner:
        return doc.permissions.get('owner', False)
    elif doc.group in user.groups:
        return doc.permissions.get('group', False)
    else:
        return doc.permissions.get('other', False)
```

## 4. 結果：「検索対象となる文書集合がユーザーごとに異なるRAGを実現」

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

## 5. 実用化にむけて

本サンプルでは、データのアクセス権限をベクトルDB構築時のメタデータに埋め込むことで、ユーザーごとのRAG検索制御を実現している。しかし、この方式では、権限変更があった場合に即座に反映されないという制約がある。

この課題に対応するためには、以下のような設計が考えられる：

1. **権限管理とデータ本体を分離する設計**  
   ベクトルDBには文書の参照IDやURLのみを格納し、検索後にオリジナルデータへアクセスする際に最新のアクセス権限を確認する方式を取ることで、柔軟な運用が可能となる。

2. **動的な認可チェックの導入**  
   検索結果の文書ごとに、外部のアクセス制御サービスに照会してリアルタイムに認可を行うことで、常に最新の権限を反映できる。

3. **キャッシュや認可ログとの統合**  
   アクセス権のキャッシュを活用しつつ、監査ログや理由の記録と統合することで、安全性とパフォーマンスを両立する構成も考えられる。

RAGシステムにおいて、柔軟な情報取得とアクセス制御の両立を実現するためには、検索段階での制御設計が重要であることが確認できる。
