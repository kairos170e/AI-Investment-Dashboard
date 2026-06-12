# data_fetcher.py

import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from urllib.parse import quote
import re

import streamlit as st
import pandas as pd
import yfinance as yf
import requests


@st.cache_data(ttl=3600)
def get_stock_data(ticker: str, period: str = "6mo") -> pd.DataFrame:
    """
    取得股票歷史資料

    使用 yfinance 的 Ticker().history() 取得資料，
    避免新版 yf.download() 產生 MultiIndex 欄位問題。

    參數:
        ticker (str): 股票代碼，例如 AAPL、2330.TW
        period (str): 查詢期間，例如：
                      1mo、3mo、6mo、1y、2y、5y

    回傳:
        pd.DataFrame

        欄位固定為：
        Open, High, Low, Close, Volume

        index:
        日期索引(DateTimeIndex)

        發生錯誤或查無資料時回傳空 DataFrame
    """
    try:
        ticker = ticker.strip()

        if not ticker:
            return pd.DataFrame()

        stock = yf.Ticker(ticker)

        history_df = stock.history(period=period)

        if history_df.empty:
            return pd.DataFrame()

        required_columns = ["Open", "High", "Low", "Close", "Volume"]

        missing_columns = [
            column
            for column in required_columns
            if column not in history_df.columns
        ]

        if missing_columns:
            return pd.DataFrame()

        result_df = history_df[required_columns].copy()

        return result_df

    except Exception:
        return pd.DataFrame()


def _strip_html(text: str) -> str:
    """移除字串中的 HTML 標籤（Google News RSS 的 description 會夾雜 <a> 等標籤）。"""
    return re.sub(r"<[^>]+>", "", text or "").strip()


def _to_iso(date_str: str) -> str:
    """
    把 RSS 的 pubDate（RFC 2822 格式）轉成 ISO 8601 字串。

    範例:
        "Wed, 11 Jun 2026 08:00:00 GMT" → "2026-06-11T08:00:00+00:00"

    轉換失敗時原樣回傳。
    """
    try:
        return parsedate_to_datetime(date_str).isoformat()
    except Exception:
        return date_str or ""


@st.cache_data(ttl=3600)
def get_news(query: str, max_items: int = 8) -> list[dict]:
    """
    取得新聞資料

    使用 Google News RSS 查詢新聞（免金鑰）。
    以繁體中文台灣版搜尋，適合查詢台股與美股相關新聞。

    注意：
    此版本不需要 API Key，直接呼叫即可。

    參數:
        query (str): 搜尋關鍵字，例如 2330.TW、AAPL
        max_items (int): 最大新聞數量

    回傳:
        list[dict]

        每個 dict 格式固定：

        {
            "title": str,
            "description": str,
            "url": str,
            "publishedAt": str  ← ISO 8601 格式
        }

        發生錯誤時回傳 []
    """
    try:
        query = query.strip()

        if not query:
            return []

        # hl/gl/ceid 指定繁中台灣版；query 需 URL 編碼
        url = (
            "https://news.google.com/rss/search?"
            f"q={quote(query)}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        )

        response = requests.get(url, timeout=10)

        response.raise_for_status()

        # 用內建 xml.etree 解析 RSS，不引入規範外的套件
        root = ET.fromstring(response.content)

        news_list = []

        for item in root.iter("item"):
            title = (item.findtext("title") or "").strip()

            if not title:
                continue

            news_list.append(
                {
                    "title": title,
                    "description": _strip_html(item.findtext("description") or ""),
                    "url": (item.findtext("link") or "").strip(),
                    "publishedAt": _to_iso(item.findtext("pubDate") or ""),
                }
            )

            if len(news_list) >= max_items:
                break

        return news_list

    except Exception:
        return []


# ==================================================
# 簡單測試
# ==================================================
if __name__ == "__main__":

    print("=== 股票資料測試 ===")

    stock_df = get_stock_data("AAPL")

    print(stock_df.head())

    print("\n=== 新聞測試 ===")

    news = get_news("Apple")

    print(f"新聞數量: {len(news)}")

    if news:
        print(news[0])
