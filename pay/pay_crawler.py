from hashlib import new
import sys
import os
import time
import datetime
import traceback
import boto3
import pathlib
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import requests
import urllib.parse
import argparse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
current_dir = pathlib.Path(__file__).parent
sys.path.append("../util")
import util
import crawler_base as cb



class PaypayCrawler(cb.SeleniumCralwer):
    platform = "paypay"
    s3_session = boto3.Session(profile_name="resale-app-crawling")
    s3_bucket = s3_session.resource("s3").Bucket("resale-app-crawling")
    s3_output_dir = pathlib.Path(f"crawler/{platform}")


    def __init__(self, is_test=False, wait_sec=1.0, headless=True):
        super().__init__(
            is_test=is_test, 
            wait_sec=wait_sec,
            headless=headless
        )
        self.max_wait_sec = 20


    def crawl_url(self, start_url):
        items = []
        next_url = start_url
        current_page = 0

        self.logger.info(f"Start crawling: {start_url}")
        while True:
            self.get_url(next_url)

            # wait until the item area is loaded
            try:
                WebDriverWait(self.driver, self.max_wait_sec).until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '#itm')),
                        EC.presence_of_element_located((By.TAG_NAME,"a"))
                    )
                )

            except Exception as e:
                self.logger.error("Timeout occurred while loading the page.")
                self.logger.error(traceback.format_exc())
                break

            page_source = self.get_page_source()
            if page_source is None:
                self.logger.error(f"Failed to access the next page: {next_url}")
                break

            new_items = self.parse_items(page_source)
            print(new_items)
            if len(new_items) == 0:
                self.logger.warning(f"No items found: {next_url}")
                break
            
            items += new_items

            next_url = self.get_next_url(start_url, current_page)
            if next_url is None:
                break

            if self.is_test and current_page >= 2:
                break

            current_page += 1

        self.logger.info(f"Finish crawling: {start_url}")
        new_df = pd.DataFrame(items)

        return new_df


    def parse_items(self, html):
        items = []
        try:
            #tmb_elems= driver.find_element(By.CSS_SELECTOR, '#itm')
            #elements = tmb_elems.find_elements(By.TAG_NAME,"a") 
            if len(item_area) == 0:
                return items

            for element in elements:
                items.append(element.get_attribute("href"))

        except Exception as e:
            self.logger.error(f"An error occurred while parsing items.")
            self.logger.error(traceback.format_exc())

        return items


    def parse_item_info(self, item):
        driver = webdriver.Chrome()
        driver.get(item)
        tmb_elems= driver.find_element(By.CSS_SELECTOR, '#itm')
        elements = tmb_elems.find_elements(By.TAG_NAME,"a") 
        item_info = {}

        try:
            # item id
            
            item_info["item_id"] = element.get_attribute("href").split("/")[-1]

            # item name
            item_info["item_name"] = element.find_element(By.TAG_NAME,"img").get_attribute("alt")

            # price
            item_info["price"] = element.find_element(By.CLASS_NAME, "ItemThumbnail__Price-tlgyjt-3").text

            # is soldout
            #sticker = thumbnail.get("sticker", None)
            #item_info["is_soldout"] = (sticker == "sold")

            # parse datetime
            #item_info["crawl_date"] = util.get_jst_time()

        except Exception as e:
            self.logger.error(f"Failed to parse an item.")
            self.logger.error(traceback.format_exc())

        return item_info
    


    def get_next_url(self, start_url, current_page):
        try:
            q = urllib.parse.urlparse(start_url)
            qs_d = urllib.parse.parse_qs(q.query)
            qs_d["page"] = f"v1:{current_page+1}"  ##urlのどこ変えるか

        except Exception as e:
            return None

        return urllib.parse.urlunparse(
            q._replace(query=urllib.parse.urlencode(qs_d, doseq=True))
        )


if __name__ == "__main__":
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--url_path")
    args, leftovers = parser.parse_known_args()
    """
    url_df = pd.read_csv("../pay/util/test/test_paypay_urls.csv")#戻す
    crawler = PaypayCrawler(is_test=True, headless=False)
    crawler.run_crawler(url_df["url"])
