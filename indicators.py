# indicators.py
# 負責人：量化邏輯與指標演算法
# 功能：接收 OHLCV 資料，計算技術指標後回傳擴充後的 DataFrame

import pandas as pd
import numpy as np
import pandas_ta_classic as ta


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    計算技術指標並附加到輸入的 DataFrame。

    輸入：
        df (pd.DataFrame)：含 Open / High / Low / Close / Volume 欄位的 DataFrame，
                           通常由 data_fetcher 模組提供。

    新增欄位（沿用 pandas_ta 預設名稱）：
        - SMA_20        ：20 日簡單移動平均線
        - SMA_60        ：60 日簡單移動平均線
        - RSI_14        ：14 日相對強弱指標
        - MACD_12_26_9  ：MACD 主線
        - MACDh_12_26_9 ：MACD 柱狀圖（Histogram）
        - MACDs_12_26_9 ：MACD 訊號線（Signal）

    回傳：
        pd.DataFrame：原本的 OHLCV 欄位全部保留，再加上上述指標欄位。
                      若資料不足或發生錯誤，缺少的指標欄位會以 NaN 填入。

    注意事項：
        - 使用 try-except 全面保護，任何情況下都不會對外拋出例外。
        - 若傳入空的 DataFrame，直接回傳原 df，不會崩潰。
    """

    # ── 防呆：輸入為空或不是 DataFrame，直接回傳原樣 ──────────────────────
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df

    # ── 確認必要欄位是否存在 ──────────────────────────────────────────────
    required_columns = {"Open", "High", "Low", "Close", "Volume"}
    if not required_columns.issubset(df.columns):
        # 缺少必要欄位，無法計算，直接回傳原 df
        return df

    # ── 複製一份，避免修改到呼叫端的原始資料 ─────────────────────────────
    result_df = df.copy()

    # ── 計算 SMA_20（20 日簡單移動平均線）────────────────────────────────
    try:
        sma_20 = ta.sma(result_df["Close"], length=20)
        # pandas_ta 回傳一個 Series，名稱即為 "SMA_20"
        result_df["SMA_20"] = sma_20
    except Exception:
        # 計算失敗時給 NaN 欄位，確保 DataFrame 格式一致
        result_df["SMA_20"] = np.nan

    # ── 計算 SMA_60（60 日簡單移動平均線）────────────────────────────────
    try:
        sma_60 = ta.sma(result_df["Close"], length=60)
        result_df["SMA_60"] = sma_60
    except Exception:
        result_df["SMA_60"] = np.nan

    # ── 計算 RSI_14（14 日相對強弱指標）──────────────────────────────────
    try:
        rsi_14 = ta.rsi(result_df["Close"], length=14)
        result_df["RSI_14"] = rsi_14
    except Exception:
        result_df["RSI_14"] = np.nan

    # ── 計算 MACD（12/26/9 參數）─────────────────────────────────────────
    try:
        macd_df = ta.macd(result_df["Close"], fast=12, slow=26, signal=9)
        # pandas_ta 回傳一個含三欄的 DataFrame：
        #   MACD_12_26_9、MACDh_12_26_9、MACDs_12_26_9
        if macd_df is not None and not macd_df.empty:
            # 逐欄合併，只取我們要的三欄
            for col in ["MACD_12_26_9", "MACDh_12_26_9", "MACDs_12_26_9"]:
                if col in macd_df.columns:
                    result_df[col] = macd_df[col].values
                else:
                    result_df[col] = np.nan
        else:
            # macd_df 為 None 或空，補 NaN
            for col in ["MACD_12_26_9", "MACDh_12_26_9", "MACDs_12_26_9"]:
                result_df[col] = np.nan
    except Exception:
        for col in ["MACD_12_26_9", "MACDh_12_26_9", "MACDs_12_26_9"]:
            result_df[col] = np.nan

    return result_df


# ══════════════════════════════════════════════════════════════════════════════
# 以下為簡單測試，確認程式能正常執行
# 執行方式：在終端機輸入 python indicators.py
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import random

    print("=" * 60)
    print("【測試 1】正常資料（100 筆），應可算出 SMA_20 / RSI，SMA_60 前幾筆為 NaN")
    print("=" * 60)

    # 建立 100 筆假的 OHLCV 資料（模擬股價走勢）
    random.seed(42)
    np.random.seed(42)

    n = 100
    close_prices = 100 + np.cumsum(np.random.randn(n))  # 隨機遊走價格
    fake_data = pd.DataFrame(
        {
            "Open":   close_prices * (1 + np.random.uniform(-0.005, 0.005, n)),
            "High":   close_prices * (1 + np.random.uniform(0.000, 0.010, n)),
            "Low":    close_prices * (1 - np.random.uniform(0.000, 0.010, n)),
            "Close":  close_prices,
            "Volume": np.random.randint(1_000_000, 5_000_000, n),
        }
    )

    result = add_indicators(fake_data)

    # 印出最後 5 筆，確認指標欄位存在且有數值
    indicator_cols = [
        "Close",
        "SMA_20",
        "SMA_60",
        "RSI_14",
        "MACD_12_26_9",
        "MACDh_12_26_9",
        "MACDs_12_26_9",
    ]
    print(result[indicator_cols].tail(5).to_string())
    print()
    print(f"✅ 回傳 DataFrame 欄位數：{len(result.columns)}（原 5 欄 + 指標 6 欄 = 11 欄）")
    print(f"✅ 原 OHLCV 欄位完整保留：{list(fake_data.columns) == list(result.columns[:5])}")
    print()

    # ── 測試 2：資料筆數不足（只有 10 筆），SMA_60 應全為 NaN ──────────────
    print("=" * 60)
    print("【測試 2】資料只有 10 筆，SMA_60 應全部為 NaN")
    print("=" * 60)

    small_data = fake_data.head(10).copy()
    result_small = add_indicators(small_data)
    print(result_small[indicator_cols].to_string())
    print()
    print(f"✅ SMA_60 全為 NaN：{result_small['SMA_60'].isna().all()}")
    print()

    # ── 測試 3：空的 DataFrame，應直接回傳原樣不崩潰 ─────────────────────
    print("=" * 60)
    print("【測試 3】空的 DataFrame，應直接回傳，不崩潰")
    print("=" * 60)

    empty_df = pd.DataFrame()
    result_empty = add_indicators(empty_df)
    print(f"✅ 傳入空 df，回傳也是空 df：{result_empty.empty}")
    print()

    # ── 測試 4：缺少必要欄位，應直接回傳原樣不崩潰 ──────────────────────
    print("=" * 60)
    print("【測試 4】缺少 Volume 欄位，應直接回傳原 df，不崩潰")
    print("=" * 60)

    bad_df = fake_data.drop(columns=["Volume"])
    result_bad = add_indicators(bad_df)
    print(f"✅ 欄位與輸入相同（未被修改）：{list(result_bad.columns) == list(bad_df.columns)}")
    print()

    print("=" * 60)
    print("所有測試完成，程式運作正常！")
    print("=" * 60)
