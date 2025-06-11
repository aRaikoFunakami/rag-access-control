# Slack メッセージをアクセス制御付きで ChromaDB に埋め込む

Slackチャンネル内のメッセージを、**アクセス可能ユーザー情報とともにベクトル化し、ChromaDBに保存**します。また、**保存したデータをSlack APIを使ってユーザー名やチャンネル名に変換して可視化**する方法も紹介します。

---

## Slack API の準備

### 1. Slack App を作成

Slack API 管理ページ（[https://api.slack.com/apps](https://api.slack.com/apps)）で新しいアプリ (api_test) を作成します。

### 2. 必要な OAuth スコープを追加

**api_test** アプリの　`OAuth & Permissions` ページから、以下の **Bot Token Scopes** を追加します：

| スコープ          | 説明                               |
|-------------------|------------------------------------|
| `channels:history`| パブリックチャンネルの履歴取得     |
| `groups:history`  | プライベートチャンネルの履歴取得   |
| `channels:read`   | チャンネル情報の取得               |
| `users:read`      | ユーザー情報の取得                 |

- 追加後、ワークスペースに再インストールしてください。
- テストに使いたいチャネルに **api_test** アプリを追加します

### 3. Slack Bot Token を環境変数 `.env` に保存

```env
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## Slack のデータを埋め込む

`slack_embedding_message.py` を実行することで、**api_test**アプリを追加した Slack チャンネルのメッセージとアクセス制御情報を取得し、ChromaDB に埋め込みます。


### データとアクセス権限の埋め込み

```bash
uv run slack_embedding_message.py
```

実行結果例：

```bash
合計 4 件のメッセージを Chroma に埋め込みました
```

`.chroma` ディレクトリに保存されます。

---

## 埋め込みデータの内容を確認する

`slack_show_messages.py` を実行することで、ChromaDB に埋め込んだSlackメッセージとそのメタデータを確認できます。
テスト用にデータ埋め込み時とチャネルにアクセス可能なメンバーを変更しておく。今回の場合には、`access-test` チャネルから **rairaii** ユーザーが退出しておいた。

```bash
uv run slack_show_messages.py
```

### 実行結果の例

`access-test` チャネルと `非公開テストチャネル` チャネルのデータが確かに埋め込まれていることが確認できる。
`access-test` チャネルの Permitted Users がデータ埋め込み時と最新の状態に変更があることが確認できる。

`Permitted Users (Saved)` : データ埋め込み時のアクセス可能なユーザ
`Permitted Users (Latest)`: 現時点でのアクセス可能なユーザ

```bash
Chroma に保存された Slack メッセージの埋め込み内容を確認します...
--- Slack Document 1 ---
Text: <@U090YFVS29G>さんがチャンネルに参加しました
Metadata:
  - Channel: access-test (C090VQYL7PF)
  - Channel Type: public
  - Posted By: api_test
  - Permitted Users (Saved): rairaii, api_test
  - Permitted Users (Latest): api_test

--- Slack Document 2 ---
Text: <@U090Y4B4MEG>さんがチャンネルに参加しました
Metadata:
  - Channel: access-test (C090VQYL7PF)
  - Channel Type: public
  - Posted By: rairaii
  - Permitted Users (Saved): rairaii, api_test
  - Permitted Users (Latest): api_test

--- Slack Document 3 ---
Text: <@U090YFVS29G>さんがチャンネルに参加しました
Metadata:
  - Channel: 非公開テストチャネル (C090VR527TP)
  - Channel Type: private
  - Posted By: api_test
  - Permitted Users (Saved): rairaii, api_test
  - Permitted Users (Latest): rairaii, api_test

--- Slack Document 4 ---
Text: <@U090Y4B4MEG>さんがチャンネルに参加しました
Metadata:
  - Channel: 非公開テストチャネル (C090VR527TP)
  - Channel Type: private
  - Posted By: rairaii
  - Permitted Users (Saved): rairaii, api_test
  - Permitted Users (Latest): rairaii, api_test
```


---

## SlackチャンネルにBotが未参加の場合の注意

Slackの仕様により、**Botが参加していないチャンネルのメッセージは取得できません**。次のようにチャンネルでBotを招待してください：

```slack
/invite @api_test
```

