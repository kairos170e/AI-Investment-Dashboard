# database_manager.py

import sqlite3


DB_PATH = "watchlist.db"


def _initialize_database() -> None:
    """
    初始化資料庫與 watchlist 資料表

    若資料表不存在則自動建立：
    - id：主鍵
    - ticker_symbol：股票代碼（唯一值）
    - date_added：新增時間
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS watchlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker_symbol TEXT UNIQUE NOT NULL,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()

    except Exception:
        pass


def add_ticker(ticker: str) -> bool:
    """
    新增股票代碼至 watchlist

    參數:
        ticker (str): 股票代碼，例如 AAPL、2330.TW
                      輸入自動轉大寫（aapl → AAPL）

    回傳:
        bool
        - True：新增成功
        - False：空字串、已存在或發生錯誤
    """
    try:
        # [修正] 統一轉大寫，避免 AAPL 與 aapl 被視為不同代碼
        ticker = ticker.strip().upper()

        if not ticker:
            return False

        _initialize_database()

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # 檢查是否已存在
            cursor.execute(
                """
                SELECT 1
                FROM watchlist
                WHERE ticker_symbol = ?
                """,
                (ticker,)
            )

            if cursor.fetchone():
                return False

            # 新增資料
            cursor.execute(
                """
                INSERT INTO watchlist (ticker_symbol)
                VALUES (?)
                """,
                (ticker,)
            )

            conn.commit()

        return True

    except Exception:
        return False


def get_watchlist() -> list[str]:
    """
    取得目前自選股清單

    回傳:
        list[str]
        例如：
        ["2330.TW", "AAPL"]

        依新增順序（id）排列，確保順序穩定。
        若無資料或發生錯誤則回傳 []
    """
    try:
        _initialize_database()

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # [修正] 改用 id 排序，避免同一秒新增時順序不穩
            cursor.execute("""
                SELECT ticker_symbol
                FROM watchlist
                ORDER BY id ASC
            """)

            rows = cursor.fetchall()

            return [row[0] for row in rows]

    except Exception:
        return []


def remove_ticker(ticker: str) -> bool:
    """
    從 watchlist 刪除指定股票代碼

    參數:
        ticker (str): 股票代碼
                      輸入自動轉大寫（aapl → AAPL）

    回傳:
        bool
        - True：成功刪除
        - False：找不到資料或發生錯誤
    """
    try:
        # [修正] 統一轉大寫，與新增時一致
        ticker = ticker.strip().upper()

        if not ticker:
            return False

        _initialize_database()

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                DELETE FROM watchlist
                WHERE ticker_symbol = ?
                """,
                (ticker,)
            )

            deleted_count = cursor.rowcount

            conn.commit()

            return deleted_count > 0

    except Exception:
        return False


# ==================================================
# 簡單測試
# ==================================================
if __name__ == "__main__":

    print("=== 新增測試 ===")
    print(add_ticker("AAPL"))
    print(add_ticker("2330.TW"))
    print(add_ticker("AAPL"))   # 重複資料 → False
    print(add_ticker("aapl"))   # 小寫重複 → False（修正後）

    print("\n=== 目前 Watchlist ===")
    print(get_watchlist())

    print("\n=== 刪除測試 ===")
    print(remove_ticker("aapl"))   # 小寫輸入也能刪（修正後）

    print("\n=== 刪除後 Watchlist ===")
    print(get_watchlist())
