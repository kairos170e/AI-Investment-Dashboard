"""AI 新聞情緒分析 —— 負責人：呂昇峰
目前是「臨時版」，回傳固定結果讓畫面能跑。
TODO（呂昇峰）：請串接 OpenAI（金鑰用 st.secrets["OPENAI_API_KEY"]），
用少樣本 prompt 強制模型只回傳 JSON，再 json.loads（外面包 try-except）。
★ 函式名稱與回傳格式不可更改（見介面契約）。confidence 一律 0~100 整數。
"""


def analyze_sentiment(news_text: str) -> dict:
    """輸入一則新聞文字，回傳：
    {"sentiment": "positive"/"neutral"/"negative", "confidence": 0~100 整數, "summary": 繁中一句話}
    任何失敗（API 出錯、模型回傳的不是合法 JSON）都回傳中性結果，不可丟例外。
    """
    try:
        # --- 臨時假邏輯：實際應呼叫 LLM ---
        return {
            "sentiment": "neutral",
            "confidence": 50,
            "summary": "（測試結果）目前為臨時版，尚未串接真正的 AI 分析。",
        }
    except Exception as e:
        print(f"[analyze_sentiment] 發生錯誤：{e}")
        return {"sentiment": "neutral", "confidence": 0, "summary": "分析失敗，請稍後再試"}
