JSON APIの仕様
=============
バージョン: 0.1.1

データエンコーディング
----------------------
データエンコーディングについて明記されていない場合は、そのリクエスト及び応答はUTF-8でエンコードされているものとする。
無効な文字が含まれていた場合の動作は未定義とする。

リクエスト
----------
### プロトコル
リクエストはHTTPのGET,POSTメソッドを利用する。

レスポンス
----------
### 形式
レスポンスのフォーマットについて言及していない場合は、JSON形式のレスポンスを返す。
解釈できない形式のレスポンスが得られた場合はエラーが起きたと解釈しなさい。
### HTTPステータスコード
サーバはリクエストの処理が成功した時はHTTPステータスコードが2xxの応答を返す。
失敗した場合はHTTPステータスコードが4xx又は5xxの応答を返す。
### リダイレクト
HTTPステータスコードが3xxの応答が得られた場合、支持に従いリダイレクトを行いなさい。
### ページング
サーバの都合で一回のリクエストで全ての情報が得られない場合がある。その場合、支持に従い何度かリクエストを行うことで全ての情報が得られる。

独自型
------
本仕様書の解説のための独自の型をここで定義する。
### Array(X)
型名`X`の配列である。
### UINT
正の整数値を意味する。
### TIMESTAMP
時刻をUNIX TIMEをUINT型で表現した値を表す。
例えばTIMESTAMPが`1000000000`は時刻`2001-09-09T01:46:40(UTC)`を意味する。
### THREAD
```
{
    "id": UINT,
    "title": String,
    "timestamp": TIMESTAMP
    "records": UINT
}
```
属性名              | 区分  | 型                | 説明
--------------------|-------|-------------------|-----
id                  | 必須  | UINT              | ノードが保持するスレッドを一意に識別する番号。
title               | 必須  | String            | スレッドのタイトル。
timestamp           | 必須  | TIMESTAMP         | そのスレッドの最終書き込み日時。未取得のスレッドは0となる。
records             | 必須  | UINT              | そのスレッドが保持している書き込み数。未取得のスレッドは0となる。

### RECORD\_INFO
```
{
    "id": String,
    "timestamp": TIMESTAMP
}
```
属性名              | 区分  | 型                | 説明
--------------------|-------|-------------------|-----
id                  | 必須  | String            | idは重複する可能性がある。
timestamp           | 必須  | TIMESTAM          | 書き込み時刻を表す。
スレッド内のレコードはthread\_idとidとtimestampと組み合わせてレコードを一意に識別する。

### RECORD
```
{
    "id": String,
    "timestamp": TIMESTAMP,
    "name": String,
    "mail": String,
    "body": String,
    "attach": Boolean,
    "suffix": String
}
```
RECORD\_INFOにname,mail,body,attach,suffixを追加した型である。
なお、suffixは添付ファイルの拡張子である。

API.versions
-----------
利用可能なAPIのバージョンのリストを返す。
### リクエスト
`GET /api/versions`
### レスポンス
```json
{
    "versions":[
        "0.1"
    ]
}
```

API.threads.get
---------------
全てのスレッドの一覧を返す
### リクエスト
`GET /api/v0.1/threads`
#### パラメータ(任意)
属性名              | 区分  | 型                | 説明
--------------------|-------|-------------------|-----
limit               | 任意  | UINT              | 応答に含まれるスレッド数の上限を指定する
start\_time         | 任意  | TIMESTAMP         | 最終書き込み時刻の下限を指定する
end\_time           | 任意  | TIMESTAMP         | 最終書き込み日時の上限を指定する
title               | 任意  | String            | タイトルを指定する。
### レスポンス
```json
{
    "threads": Array(THREAD)
}
```
属性名              | 区分  | 型                | 説明
--------------------|-------|-------------------|-----
threads             | 必須  | Array(THREAD)     | スレッドの一覧を返す。

API.threads.head
----------------
指定したスレッドが存在するかどうかを返す
### リクエスト
`HEAD /api/v0.1/threads?title=<title>`
### レスポンス
本文は無い。
指定したスレッドのrecordsが1以上であればスレッドは存在するとみなし2xxの応答を返し、recordsが0であればスレッドは存在しないとみなし4xxの応答を返す。

API.threads.post
----------------
指定した名前のスレッドを作成する
### リクエスト
`POST /api/v0.1/threads`
### パラメータ
```
属性名              | 区分  | 型                | 説明
--------------------|-------|-------------------|-----
title               | 必須  | String            | スレッド名
```
### レスポンス
```json
{
    "thread": THREAD
}
```
属性名              | 区分  | 型                | 説明
--------------------|-------|-------------------|-----
thread              | 必須  | THREAD            | 作成したスレッド

API.records.head
----------------
指定したレコードが存在するかを返す。
### リクエスト
`HEAD /api/v0.1/records/<thread_id>/<timestamp>/<record_id>`
### レスポンス
応答に本文は無い。レコードが存在する場合はHTTPステータスコードが2xxの応答を返し、存在しない場合には4xxを返す

API.records.get
---------------
スレッド内の条件にマッチする全てのレコードを返す。
### リクエスト
`GET /api/v0.1/records/<thread_id>`
`GET /api/v0.1/records/<thread_id>/<tiimestamp>/<record_id>`
### パラメータ
属性名              | 区分  | 型                | 説明
--------------------|-------|-------------------|-----
limit               | 任意  | UINT              | 応答に含まれるスレッド数の上限を指定する
start\_time         | 任意  | TIMESTAMP         | 取得する書き込み時刻の下限を指定する
end\_time           | 任意  | TIMESTAMP         | 取得する書き込み日時の上限を指定する
id                  | 任意  | ID                | レコードのIDを指定する。結果は複数になることがある。
### レスポンス
```json
{
    "records": Array(RECORD)
}
```

API.records.post
----------------
スレッドに投稿する
### リクエスト
`POST /api/v0.1/record/<thread_id>`
### パラメータ
```
{
    "name": String,
    "mail": String,
    "body": String,
    "attach": Binary,
    "attach_sfx": String
}
```
### レスポンス
成功した場合は本文無しの応答を返す。

API.attach.head
---------------
### リクエスト
`HEAD /api/v0.1/attach/<thread_id>/<timestamp>/<record_id>`
### レスポンス
応答に本文は無い。レコードが存在する場合はHTTPステータスコードが2xxの応答を返し、存在しない場合には4xxを返す
スレッド内の指定されたレコードに添付されているファイルが存在するかを返す。

API.attach.get
--------------
スレッド内の指定されたレコードに添付されているファイルを返す。
応答は任意のデータである。
### リクエスト
`GET /api/v0.1/attach/<thread_id>/<timestamp>/<record_id>`
### レスポンス
本文は添付されたファイルの内容である。
任意の長さ・形式のデータである。

<!--
# vim ft=markdown expandtab
-->
