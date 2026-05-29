"""量化指標 —— 負責人：王仱婕
目前是「臨時版」，只先把指標欄位加上去（值為 NaN）讓格式正確、畫面能跑。
TODO（王仱婕）：請用 pandas_ta 算出真正的 SMA / RSI / MACD。
★ 函式名稱與回傳格式不可更改（見介面契約）。
★ pandas_ta 在 numpy 2.0 以上會壞，我們已用 numpy<2.0 鎖定，不要升級 numpy。
"""
import pandas as pd
import numpy as np

# 介面契約規定要新增的欄位（沿用 pandas_ta 預設命名）
_INDICATOR_COLS = [
    "SMA_20", "SMA_60", "RSI_14",
    "MACD_12_26_9", "MACDh_12_26_9", "MACDs_12_26_9",
]


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """輸入含 OHLCV 的 DataFrame，回傳同一個 df 並加上指標欄位。
    若輸入為空或資料筆數不足，直接回傳原 df（不可丟例外）。
    """
    try:
        if df is None or df.empty:
            return df if df is not None else pd.DataFrame()

        # TODO：改成真正計算，例如：
        #   import pandas_ta as ta
        #   df.ta.sma(length=20, append=True)
        #   df.ta.sma(length=60, append=True)
        #   df.ta.rsi(length=14, append=True)
        #   df.ta.macd(append=True)
        for col in _INDICATOR_COLS:
            if col not in df.columns:
                df[col] = np.nan
        return df
    except Exception as e:
        print(f"[add_indicators] 發生錯誤：{e}")
        return df
