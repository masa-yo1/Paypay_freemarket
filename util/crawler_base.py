import sys
import os
import time
import datetime
import traceback
import boto3
import pathlib
import urllib.parse
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import requests
import csv
import json
import multiprocessing as mp
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
current_dir = pathlib.Path(__file__).parent
import util


class CrawlerBase(object):
    platform = None
    s3_bucket = None
    s3_output_dir = None


    def __init__(self, is_test=False, wait_sec=1.0):
        self.is_test = is_test
        self.wait_sec = wait_sec
        self.temp_dir = current_dir / "../temp/" / self.platform
        self.temp_dir.mkdir(exist_ok=True, parents=True)
        log_dir = current_dir / f"../logs/{self.platform}/crawler/"
        self.logger = util.Logger.setup_logger(
            logger_name=__name__, 
            log_dir=log_dir
        )


    def run_crawler(self, urls):
        self.start_crawler(urls)
        df = None

        for url in urls:
            new_df = self.crawl_url(url)
            if df is None:
                df = new_df
            else:
                df = pd.concat([df, new_df])

        filename = f"{util.get_jst_time_str()}.csv"
        local_output_path = self.temp_dir / filename
        s3_output_path = self.s3_output_dir / filename

        df.to_csv(local_output_path, index=False)
        upload_success = util.s3_upload_file(
            self.s3_bucket, 
            local_output_path, 
            s3_output_path
        )

        if upload_success:
            local_output_path.unlink()
        else:
            self.logger.error(
                f"Failed to upload the crawled items to S3. platform: {self.platform}"
            )

        self.finish_crawler()


    def crawl_url(self, url):
        raise NotImplementedError("This method should be overridden.")


    def start_crawler(self, urls):
        url_list_str = "\n".join(urls)
        self.logger.info(f"Start crawling {self.platform}. URLs:\n{url_list_str}")


    def finish_crawler(self):
        self.logger.info(f"Finish crawling {self.platform}.")


class SeleniumCralwer(CrawlerBase):
    """
    Crawler for the pages that depend on javascript
    """
    def __init__(self, is_test=False, wait_sec=1.0, chromedriver_path=None, headless=True):
        super().__init__(is_test=is_test, wait_sec=wait_sec)

        if chromedriver_path is None:
            self.chromedriver_path = current_dir / "webdriver/chromedriver"
        else:
            self.chromedriver_path = chromedriver_path

        self.headless = headless

    
    def get_session_selenium(self):
        # open chrome
        desired_capabilities = \
            webdriver.common.desired_capabilities.DesiredCapabilities.CHROME.copy()
        options = Options()

        if self.headless:
            options.add_argument("--headless")
        
        driver = webdriver.Chrome(
            executable_path=str(self.chromedriver_path),
            desired_capabilities=desired_capabilities,
            chrome_options=options)

        return driver


    def get_url(self, url, wait_sec=0, num_retry=3):
        for r in range(num_retry):              
            try:
                self.driver.get(str(url))
                time.sleep(wait_sec)
                break
            
            except Exception as e:
                logger.error(e)
                return None
        
        return self.driver.page_source


    def get_page_source(self):
        return self.driver.page_source


    def save_response_html(self, url, html_path):
        try:
            page_source = self.get_url(url)
            pathlib.Path(html_path).parent.mkdir(exist_ok=True, parents=True)
            with open(html_path, "w", encoding="UTF-8") as f:
                f.write(page_source)

            return True

        except Exception as e:
            logger.error(e)

        return False


    def scroll_down(self, max_wait_sec=60):
        """
        A method for scrolling down the current page
        """
        start_time = util.get_jst_time()

        # Get scroll height
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:
            if (util.get_jst_time() - start_time).seconds > max_wait_sec:
                self.logger.warning("Failed to scroll down to the bottom")
                return False
            
            # Scroll down to the bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            time.sleep(2)

            # Calculate new scroll height and compare with last scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                self.logger.info("Succeeded to scroll down to the bottom")
                break

            last_height = new_height

        return True


    def start_crawler(self, urls):
        url_list_str = "\n".join(urls)
        self.logger.info(f"Start crawling {self.platform}. URLs:\n{url_list_str}")
        self.driver = self.get_session_selenium()


    def finish_crawler(self):
        self.logger.info(f"Finish crawling {self.platform}.")
        self.close()


    def close(self):
        self.driver.close()


class DownloaderBase(object):
    platform = None
    base_url = None
    s3_bucket = None
    s3_output_dir = None
    wait_sec = 1.0


    def __init__(self, is_test=False, num_threads=None):
        self.is_test = is_test
        log_dir = current_dir / f"../logs/{self.platform}/downloader/"
        self.logger = util.Logger.setup_logger(
            logger_name=__name__, 
            log_dir=log_dir
        )

        if num_threads is None:
            if is_test:
                self.num_threads = 1
            else:
                self.num_threads = mp.cpu_count()

        else:
            self.num_threads = int(num_threads)


    def start_download(self, item_ids):
        self.start_downloader()
        
        if self.is_test and len(item_ids) > 5:
            item_ids = item_ids[:5]

        with mp.Pool(self.num_threads) as p:
            result = p.map(self.download_html, item_ids)

        self.finish_downloader(item_ids, result)


    @classmethod
    def download_html(cls, item_id):
        url = cls.get_item_url(item_id)
        s3_path = cls.s3_output_dir / item_id / f"{util.get_jst_time_str()}.html"
        upload_success = util.s3_save_file(url, cls.s3_bucket, s3_path)
        time.sleep(cls.wait_sec)
        
        return upload_success


    @staticmethod
    def get_item_url(item_id):
        raise NotImplementedError("This method should be overridden.")


    def start_downloader(self):
        self.logger.info(f"Start downloading htmls: {self.platform}.")


    def finish_downloader(self, item_ids, result):
        download_results = []
        for item_id, r in zip(item_ids, result):
            download_results.append(f"{item_id}: {r}")

        text = "\n".join(download_results)

        self.logger.info(f"Finish downloading htmls: {self.platform}.")
        self.logger.info(f"Upload results: \n{text}")


if __name__ == "__main__":
    pass
