"""Information about Foreign ETF."""
import json
import time
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import rootpath
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class Foreign_ETF():
    """Handle Froeign ETF."""

    __url_sbi = ("https://search.sbisec.co.jp/"
                 "v2/popwin/info/stock/pop6040_etf.html")
    __url_rakuten = ("https://www.rakuten-sec.co.jp/"
                     "web/market/search/etf_search/"
                     "?form-text-01=&mktch_us=on&mktch_hk=on&mktch_sg=on")
    __url_monex1 = ("https://mst.monex.co.jp/"
                    "mst/servlet/ITS/ucu/UsSymbolListGST")
    __url_monex1_csv = ("https://mst.monex.co.jp/"
                        "pc/pdfroot/public/50/99/Monex_US_LIST.csv")
    __url_monex2 = ("https://mst.monex.co.jp/"
                    "mst/servlet/ITS/ucu/ChinaEtfListGST")

    def upate(self, options: Options = None, monex_csv: bool = False):
        """Update securities firm infromation.

        Parameters
        ----------
        options : Options, optional
            webdriver argument, by default None
        monex_csv : bool, optional
            Use CSV data online instead of web page, by default False
        """
        options = options or Options()

        self._update_sbi()
        self._update_rakuten(options)
        if monex_csv:
            self._update_monex1_csv(options)
        else:
            self._update_monex1(options)
        self._update_monex2(options)

    def _update_sbi(self):
        res = requests.get(self.__url_sbi)
        soup = BeautifulSoup(res.content, "html.parser")

        res = soup.find_all("div", class_='accTbl01')
        df_arr = []
        for elem in res:
            df, = pd.read_html(str(elem), converters={'米国': str})
            df.columns = [
                "ticker",
                "name",
                "content",
                "market",
                "fee",
                "fact",
                "chart",
                "management"]
            df = df[df["ticker"] == df["ticker"]]
            df_arr.append(df)
        df = pd.concat(df_arr)
        df["sbi"] = "○"

        def convert(x):
            x = str(x).replace("％", "").replace("%", "")
            try:
                return float(x)
            except ValueError:
                return np.nan
        df["fee"] = df["fee"].apply(convert)
        del df["fact"]
        del df["chart"]
        del df["management"]
        del df["content"]
        df = df.reset_index()
        del df["index"]

        if len(df[df["ticker"] == "QQQ"]) > 1:
            temp = df[df["ticker"] == "QQQ"][1:]
            df = df.drop(temp.index[0])

        self.df_sbi = df

    def _update_rakuten(self, options: Options):
        browser = webdriver.Chrome(options=options)
        browser.get(self.__url_rakuten)
        time.sleep(1)
        html = browser.page_source
        browser.close()
        browser.quit()

        soup = BeautifulSoup(html, "html.parser")
        res, = soup.find_all("div", class_='table_box')

        df, = pd.read_html(str(res))
        df.columns = [
            "ticker",
            "name",
            "market",
            "date",
            "assets",
            "yield",
            "distribution",
            "fee",
            "area"]
        del df["date"]
        df["rakuten"] = "○"
        del df["assets"]
        del df["yield"]
        del df["distribution"]

        self.df_rakuten = df

    def _update_monex1(self, options: Options):
        browser = webdriver.Chrome(options=options)
        browser.get(self.__url_monex1)
        time.sleep(3)
        browser.execute_script("doEtfSearch('1')")

        df = None
        while True:
            time.sleep(1)

            html = browser.page_source
            soup = BeautifulSoup(html, "html.parser")

            res = soup.find(id="meigaraData")
            tmp, = pd.read_html(str(res))
            if df is None:
                df = tmp
            else:
                df = pd.concat([df, tmp], axis=0)

            res = soup.find("ul", class_="page-navi-list")
            res = res.findChildren()[-1]
            url = res.get("href")
            if url:
                if url.startswith("javascript:"):
                    url = url.replace("javascript:", "")
                    browser.execute_script(url)
                else:
                    browser.get(url)
            else:
                break

        browser.close()
        browser.quit()

        rows = list(df.iterrows())

        arr = []
        for (_, row1), (_, row2) in zip(rows[::2], rows[1::2]):
            # ticker, name, index, index, index,   market, fee, management
            # ticker, name, type,  area,  develop, market, fee, management
            row = {
                "ticker": row1[0],
                "name": row1[1],
                "market": row1[5],
                "fee": row1[6],
                "area": row2[3]
            }
            arr.append(row)

        self.df_monex1 = pd.DataFrame.from_records(arr)

    def _update_monex1_csv(self, options: Options):
        browser = webdriver.Chrome(options=options)
        browser.get(self.__url_monex1_csv)
        html = browser.page_source
        browser.close()
        browser.quit()

        df = pd.read_csv(
            StringIO(html),
            names=[
                "ticker",
                "name_en",
                "name",
                "market",
                "type"],
            skiprows=1)

        df = df[df.type == "ETF"]
        del df["name_en"]
        del df["type"]

        self.df_monex1 = df

    def _update_monex2(self, options: Options):
        browser = webdriver.Chrome(options=options)
        browser.get(self.__url_monex2)
        html = browser.page_source
        browser.close()
        browser.quit()

        soup = BeautifulSoup(html, "html.parser")
        res = soup.find(class_="table-block")

        df, = pd.read_html(str(res))
        df.columns = ["ticker", "area", "name", "management", "content"]

        def convert(x):
            return f"{x:0>5}"
        df.ticker = df.ticker.apply(convert)
        del df["management"]
        del df["content"]

        df["market"] = "香港"

        self.df_monex2 = df

    @property
    def df_monex(self) -> pd.DataFrame:
        """Merge `df_monex1` and `df_monex2`.

        Returns
        -------
        pd.DataFrame
            Data of Monex証券
        """
        df = pd.concat([self.df_monex1, self.df_monex2])
        df["monex"] = "○"

        return df

    @property
    def df(self) -> pd.DataFrame:
        """Merge `df_ *` of All firm.

        Returns
        -------
        pd.DataFrame
            Data of All firm.
        """
        # Use SBI as base
        df = self.df_sbi

        # Merge Rakuten
        df = pd.merge(df, self.df_rakuten, on=["ticker"], how="outer")
        df.loc[df["name_x"] != df["name_x"],
               "name_x"] = df.loc[df["name_x"] != df["name_x"], "name_y"]
        del df["name_y"]
        df.loc[df["fee_x"] != df["fee_x"],
               "fee_x"] = df.loc[df["fee_x"] != df["fee_x"], "fee_y"]
        del df["fee_y"]
        df.loc[df["market_x"] != df["market_x"],
               "market_x"] = df.loc[df["market_x"] != df["market_x"],
                                    "market_y"]
        del df["market_y"]
        df = df.rename(
            columns={
                "name_x": "name",
                "market_x": "market",
                "fee_x": "fee"})

        # Merge Monex
        df = pd.merge(df, self.df_monex, on=["ticker"], how="outer")
        df.loc[df["name_x"] != df["name_x"],
               "name_x"] = df.loc[df["name_x"] != df["name_x"], "name_y"]
        del df["name_y"]
        df.loc[df["market_x"] != df["market_x"],
               "market_x"] = df.loc[df["market_x"] != df["market_x"],
                                    "market_y"]
        del df["market_y"]
        df.loc[df["area_x"] != df["area_x"],
               "area_x"] = df.loc[df["area_x"] != df["area_x"], "area_y"]
        del df["area_y"]
        df.loc[df["fee_x"] != df["fee_x"],
               "fee_x"] = df.loc[df["fee_x"] != df["fee_x"], "fee_y"]
        del df["fee_y"]
        df = df.rename(
            columns={
                "name_x": "name",
                "market_x": "market",
                "area_x": "area",
                "fee_x": "fee"})

        df.loc[df["sbi"] != df["sbi"], "sbi"] = "×"
        df.loc[df["rakuten"] != df["rakuten"], "rakuten"] = "×"
        df.loc[df["monex"] != df["monex"], "monex"] = "×"
        df = df.fillna("NaN")

        return df

    def to_json(self) -> dict:
        """Convert `df` to `dict`.

        Returns
        -------
        dict
            Data of `df`
        """
        return {"data": self.df.to_dict('records')}

    def update_json(self, path: Path = None):
        """Update json file.

        Parameters
        ----------
        path: Path, optional
            Path to json file, by default None
        """
        path = path or Path(rootpath.detect(__file__)) / "doc" \
            / "foreign-etf.json"

        with path.open("w") as fp:
            json.dump(self.to_json(), fp, ensure_ascii=False, indent=4)
