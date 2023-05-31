import sys
import os
import time
import datetime
import traceback
import boto3
import pathlib
import numpy as np
import pandas as pd
import requests
import urllib.parse
import argparse
current_dir = pathlib.Path(__file__).parent
sys.path.append("../util")
import util
import crawler_base as cb



class PaypayDownloader(cb.DownloaderBase):
    platform = "paypay"
    base_url = "https://paypayfleamarket.yahoo.co.jp/item/"
    s3_session = boto3.Session(profile_name="resale-app-crawling")
    s3_bucket = s3_session.resource("s3").Bucket("resale-app-crawling")
    s3_output_dir = pathlib.Path(f"downloader/{platform}")
    wait_sec = 1.0


    def __init__(self, is_test=False):
        super().__init__(is_test=is_test)


    @classmethod
    def get_item_url(cls, item_id):
        return urllib.parse.urljoin(cls.base_url, item_id)


if __name__ == "__main__":
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--url_path")
    args, leftovers = parser.parse_known_args()
    """
    s3_session = boto3.Session(profile_name="resale-app-crawling")
    s3_bucket = s3_session.resource("s3").Bucket("resale-app-crawling")

    s3_url_path = "crawler/paypay/2022-06-02-22-26-32.csv"
    _, local_url_path = util.s3_download_file(s3_bucket, s3_url_path)
    item_id_df = pd.read_csv(local_url_path)
    downloader = PaypayDownloader(is_test=True)
    downloader.start_download(item_id_df["item_id"])
