# ResaleAppCrawling

## 環境構築

- まずPython環境を作成してください。
  - 可能であれば、venvで仮想環境を作成してください( https://docs.python.org/ja/3/library/venv.html )
- `requirements.txt` にあるライブラリをインストールしてください。
  - `pip3 install -r requirements.txt`
  - venvで仮想環境を作成した場合は、`source venv/bin/activate` をして、仮想環境を立ち上げてからライブラリをインストールしてください。
- Google Chromeがインストールされていない場合は、してください。
- 自分のChromeのバージョンを作成し、それに対応するchromedriverをダウンロード（ https://chromedriver.chromium.org/downloads )して、`util/webdriver/chromedriver` として保存してください。
- 自分の`ホームディレクトリ/.aws`に、slackに貼った`credentials`を追加してください。
  - Macの場合だと `/Users/[自分の名前]/.aws/credentials`

## テスト

`python3 mercari/crawler.py` および `python3 mercari/downloader.py` の両方が実行できれば環境構築成功。