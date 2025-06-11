# Google Drive に保存されたクラウドデータをアクセス制御付きで ChromaDB に埋め込む

## Google Drive と Doc の API の有効化

- [Google の API の有効化](https://console.cloud.google.com/apis/library?hl=ja&inv=1&invt=AbzzCQ&project=rag-access-control-462601)は[公式ページ](https://developers.google.com/workspace/drive/api/quickstart/python?hl=ja)を参考に行う

## Google Drive のデータを埋め込む

`googledrive_embedding_documents.py` を実行し、指定した `フォルダID` に存在する ファイル一覧 を アクセス権限 と共に取得し、ファイル内容とアクセス権限をChromaDBに埋め込む

指定したフォルダには２つのファイルが存在する

- file1 : Goodle Docファイル
- file2 : Goodle Docファイル

### データとアクセス権限の埋め込み


```bash
uv run googledrive_embedding_documents.py
```

実行結果

- フォルダID: "https://drive.google.com/drive/folders/フォルダID"
  - Google DriveのフォルダをWebブラウザで開いた時のURLから取得できる

```bash
Google Drive Folder ID を入力してください: [フォルダID]
Google Driveからファイルとパーミッションを取得中...
Please visit this URL to authorize this application: [OAuth認証URLを省略]
Embedding データを整形中...
Chroma に保存中...
[パス]/googledrive_embedding_documents.py:111: LangChainDeprecationWarning: The class `OpenAIEmbeddings` was deprecated in LangChain 0.0.9 and will be removed in 1.0. An updated version of the class exists in the :class:`~langchain-openai package and should be used instead. To use it run `pip install -U :class:`~langchain-openai` and import as `from :class:`~langchain_openai import OpenAIEmbeddings``.
  embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
[パス]/googledrive_embedding_documents.py:119: LangChainDeprecationWarning: Since Chroma 0.4.x the manual persistence method is no longer supported as docs are automatically persisted.
  vectorstore.persist()
Embedding completed and stored to Chroma DB at '.chroma'
```

### 埋め込みデータの内容を確認する

`googledrive_show_contents.py` で ChromaDB に埋め込んだメタデータを確認する

```bash
uv run googledrive_show_contents.py
```

実行結果から指定したフォルダにはファイルが２つあること、そしてそれらのアクセス権限が確認できる。

| ファイル名 | タイミング   | 種別   | アドレス/識別子     | 権限   |
|------------|--------------|--------|----------------------|--------|
| file1      | Saved        | User   | [メールアドレス]     | owner  |
| file1      | Latest       | User   | [メールアドレス]     | owner  |
| file2      | Saved        | User   | [メールアドレス]      | owner  |
| file2      | Latest       | User   | [メールアドレス]     | owner  |

- Saved: ChromaDBに埋め込んだ時のアクセス権限
- Latest: Google Driveからリアルタイムに獲得した権限


```bash
[パス]/googledrive_show_contents.py:52: LangChainDeprecationWarning: The class `OpenAIEmbeddings` was deprecated in LangChain 0.0.9 and will be removed in 1.0. An updated version of the class exists in the :class:`~langchain-openai package and should be used instead. To use it run `pip install -U :class:`~langchain-openai` and import as `from :class:`~langchain_openai import OpenAIEmbeddings``.
  embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
[パス]/googledrive_show_contents.py:53: LangChainDeprecationWarning: The class `Chroma` was deprecated in LangChain 0.2.9 and will be removed in 1.0. An updated version of the class exists in the :class:`~langchain-chroma package and should be used instead. To use it run `pip install -U :class:`~langchain-chroma` and import as `from :class:`~langchain_chroma import Chroma``.
  vectorstore = Chroma(
Total documents: 2

Authenticating with Google Drive...
Please visit this URL to authorize this application: [OAuth認証URLを省略]

--- Document 1 ---
File Name: file2
MIME Type: application/vnd.google-apps.document
File ID: [ファイルID]
['Saved Permissions in Metadata:', 'User — [メールアドレス] → Role: owner']
['Latest Permissions from Google Drive:', 'User — [メールアドレス] → Role: owner']

Summary Text:
File: file2
Type: application/vnd.google-apps.document
Content:
Hello, this is file2


--- Document 2 ---
File Name: file1
MIME Type: application/vnd.google-apps.document
File ID: [ファイルID]
['Saved Permissions in Metadata:', 'User — [メールアドレス] → Role: owner']
['Latest Permissions from Google Drive:', 'User — [メールアドレス] → Role: owner']

Summary Text:
File: file1
Type: application/vnd.google-apps.document
Content:
Hello, this is file1
```


### 最新のアクセス権限を確認する

Google Drive で `file2` のアクセス権限を変更したのち、再度アクセス権限を確認する

```bash
uv run googledrive_show_contents.py
```

`file2` に対して `Anyone` に `reader` 権限が追加されたことが確認できる

| ファイル名 | タイミング   | 種別   | アドレス/識別子     | 権限   |
|------------|--------------|--------|----------------------|--------|
| file1      | Saved        | User   | [メールアドレス]     | owner  |
| file1      | Latest       | User   | [メールアドレス]     | owner  |
| file2      | Saved        | User   | [メールアドレス]      | owner  |
| file2      | Latest       | User   | [メールアドレス]     | owner  |
| file2      | Latest       | Anyone | N/A                  | reader |

- Saved: ChromaDBに埋め込んだ時のアクセス権限
- Latest: Google Driveからリアルタイムに獲得した権限

```bash:実行結果
[パス]/googledrive_show_contents.py:52: LangChainDeprecationWarning: The class `OpenAIEmbeddings` was deprecated in LangChain 0.0.9 and will be removed in 1.0. An updated version of the class exists in the :class:`~langchain-openai package and should be used instead. To use it run `pip install -U :class:`~langchain-openai` and import as `from :class:`~langchain_openai import OpenAIEmbeddings``.
  embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
[パス]/googledrive_show_contents.py:53: LangChainDeprecationWarning: The class `Chroma` was deprecated in LangChain 0.2.9 and will be removed in 1.0. An updated version of the class exists in the :class:`~langchain-chroma package and should be used instead. To use it run `pip install -U :class:`~langchain-chroma` and import as `from :class:`~langchain_chroma import Chroma``.
  vectorstore = Chroma(
Total documents: 2

Authenticating with Google Drive...
Please visit this URL to authorize this application: [OAuth認証URLを省略]

--- Document 1 ---
File Name: file2
MIME Type: application/vnd.google-apps.document
File ID: [ファイルID]
['Saved Permissions in Metadata:', 'User — [メールアドレス] → Role: owner']
['Latest Permissions from Google Drive:', 'Anyone — N/A → Role: reader', 'User — [メールアドレス] → Role: owner']

Summary Text:
File: file2
Type: application/vnd.google-apps.document
Content:
Hello, this is file2


--- Document 2 ---
File Name: file1
MIME Type: application/vnd.google-apps.document
File ID: [ファイルID]
['Saved Permissions in Metadata:', 'User — [メールアドレス] → Role: owner']
['Latest Permissions from Google Drive:', 'User — [メールアドレス] → Role: owner']

Summary Text:
File: file1
Type: application/vnd.google-apps.document
Content:
Hello, this is file1
```