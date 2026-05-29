"""股價與新聞抓取 —— 負責人：徐宏智
目前是「臨時假資料版」，回傳少量假資料讓畫面能跑。
TODO（徐宏智）：
  - get_stock_data 改用 yf.Ticker(ticker).history(period=period)，不要用 yf.download()
  - get_news 改成串接 NewsAPI 或 GNews（金鑰用 st.secrets）
★ 函式名稱與回傳格式不可更改（見介面契約）。
"""
import pandas as pd


def get_stock_data(ticker: str, period: str = "6mo") -> pd.DataFrame:
    """回傳 OHLCV 的 DataFrame，欄位剛好為 Open, High, Low, Close, Volume，index 為日期。
    查無資料或發生錯誤時，回傳空的 DataFrame（不要回 None）。
    """
    try:
        # --- 以下為臨時假資料，之後刪掉換成 yfinance ---
        dates = pd.date_range(end=pd.Timestamp.today(), periods=10, freq="D")
        df = pd.DataFrame(
            {
                "Open":   [100, 101, 102, 101, 103, 104, 103, 105, 106, 107],
                "High":   [102, 103, 104, 103, 105, 106, 105, 107, 108, 109],
                "Low":    [99, 100, 101, 100, 102, 103, 102, 104, 105, 106],
                "Close":  [101, 102, 101, 103, 104, 103, 105, 106, 107, 108],
                "Volume": [1000, 1200, 900, 1500, 1100, 1300, 1000, 1400, 1250, 1350],
            },
            index=dates,
        )
        df.index.name = "Date"
        return df
    except Exception as e:
        print(f"[get_stock_data] 發生錯誤：{e}")
        return pd.DataFrame()


def get_news(query: str, max_items: int = 8) -> list:
    """回傳新聞列表，每筆為 dict，key 剛好為 title, description, url, publishedAt。
    發生錯誤回 []。
    """
    try:
        # --- 臨時假資料 ---
        fake = [
            {
                "title": f"（假新聞）{query} 相關利多消息",
                "description": "這是一則測試用的新聞摘要，之後會換成真實 API 回傳。",
                "url": "https://example.com/news/1",
                "publishedAt": "2026-01-01T08:00:00Z",
            },
            {
                "title": f"（假新聞）{query} 面臨庫存調整壓力",
                "description": "這是第二則測試新聞，用來驗證情緒分析與畫面顯示。",
                "url": "https://example.com/news/2",
                "publishedAt": "2026-01-01T09:00:00Z",
            },
        ]
        return fake[:max_items]
    except Exception as e:
        print(f"[get_news] 發生錯誤：{e}")
        return []
