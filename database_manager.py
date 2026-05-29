"""資料庫與基礎工程 —— 負責人：徐宏智
目前是「臨時假資料版」（用記憶體清單），讓整個 App 能先跑起來。
TODO（徐宏智）：請改成真正的 sqlite3 實作，資料表 watchlist，欄位 id / ticker_symbol / date_added。
★ 函式名稱與回傳格式不可更改（見介面契約）。
"""

# 臨時用記憶體清單代替資料庫；之後換成 SQLite
_watchlist = ["2330.TW", "AAPL"]


def add_ticker(ticker: str) -> bool:
    """新增股票代碼。成功回 True；空字串或已存在回 False。"""
    try:
        ticker = (ticker or "").strip()
        if not ticker or ticker in _watchlist:
            return False
        _watchlist.append(ticker)
        return True
    except Exception as e:
        print(f"[add_ticker] 發生錯誤：{e}")
        return False


def get_watchlist() -> list:
    """回傳目前所有股票代碼的字串列表，例如 ['2330.TW', 'AAPL']。沒資料回 []。"""
    try:
        return list(_watchlist)
    except Exception as e:
        print(f"[get_watchlist] 發生錯誤：{e}")
        return []


def remove_ticker(ticker: str) -> bool:
    """刪除股票代碼。成功回 True；找不到回 False。"""
    try:
        ticker = (ticker or "").strip()
        if ticker in _watchlist:
            _watchlist.remove(ticker)
            return True
        return False
    except Exception as e:
        print(f"[remove_ticker] 發生錯誤：{e}")
        return False
