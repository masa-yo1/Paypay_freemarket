# ResaleAppCrawling

プロジェクト名
(ここにプロジェクトの説明)

環境構築
Pythonの仮想環境を作成します。可能であれば、venv を使用してください。詳細はこちらを参照してください。

requirements.txtに記載されたライブラリをインストールします。

```bash
Copy code
pip3 install -r requirements.txt
もし venv を使用している場合は、下記のように仮想環境を有効化してからライブラリをインストールしてください。

```bash
Copy code
source venv/bin/activate
pip3 install -r requirements.txt
Google Chromeがインストールされていない場合は、インストールしてください。

自分のChromeのバージョンに対応するchromedriverをダウンロードし、util/webdriver/chromedriverとして保存してください。

自身のホームディレクトリの.awsフォルダに、slackで共有されたcredentialsを追加してください。Macの場合は、次のパスになります: /Users/[自分の名前]/.aws/credentials

テスト
下記のコマンドが実行できれば環境構築は成功です。

```bash
Copy code
python3 pay_crawler.py
python3 pay_downloader.py
