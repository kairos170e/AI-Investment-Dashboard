import json
import streamlit as st

# ==========================================
# 系統提示詞定義 (System Prompt Definition)
# ==========================================
# 此 Prompt 將 LLM 角色設定為具 CFA 資格的量化研究員，
# 提供利多與利空的 Few-Shot 範例，並強烈要求僅輸出 JSON。
SYSTEM_PROMPT = """你是一位持有 CFA（特許金融分析師）資格的資深量化研究員，專門分析金融新聞對市場與特定個股的潛在情緒影響。

請仔細閱讀使用者提供的新聞內容，並根據其對相關股票或整體市場的潛在走勢影響進行情緒分析。

請嚴格遵守以下輸出規定：
1. 僅回傳 JSON 格式的內容，絕對不可包含任何 markdown 程式碼區塊（如 ```json ... ```）、解釋性文字、前後引導句或任何額外文字。
2. 回傳的 JSON 必須剛好包含以下三個 key，且型別完全一致：
   - "sentiment": 只能是 "positive"（利多/樂觀）、"neutral"（中性/無影響）或 "negative"（利空/悲觀）其中之一。
   - "confidence": 0 到 100 之間的整數（包含 0 與 100），代表你對此分析結果的信心指數。
   - "summary": 繁體中文（Traditional Chinese）的一句話摘要，精準概括此新聞的重點。

以下是少樣本（Few-Shot）範例：

【範例一：利多（positive）】
新聞內容：台積電今日公佈最新財報，受惠於 AI 晶片需求強勁，上季營收與獲利雙雙創下歷史新高，並上調全年營收展望，預期未來兩季將持續成長。
輸出：
{"sentiment": "positive", "confidence": 95, "summary": "台積電受惠AI需求營收獲利創新高並上調全年展望。"}

【範例二：利空（negative）】
新聞內容：受高通膨與消費性電子需求疲弱影響，某半導體大廠今日宣佈下調本季營運展望，並計畫裁減全球 10% 的員工以縮減營運成本，股價隨後在盤後下跌。
輸出：
{"sentiment": "negative", "confidence": 90, "summary": "半導體大廠受需求疲弱影響下調展望並計劃裁員10%。"}

請直接分析以下新聞，並僅回傳符合上述格式的 JSON。"""


def _clean_and_parse_json(raw_text: str) -> dict:
    """
    清理 LLM 回傳的字串並將其轉換為字典。
    
    此內部輔助函式會尋找字串中第一個 '{' 與最後一個 '}' 之間的內容，
    以過濾 Markdown 程式碼框 (如 ```json ... ```) 或前後的雜亂文字。
    
    參數:
        raw_text (str): OpenAI API 回傳的原始文字
        
    回傳:
        dict: 解析成功且驗證欄位無誤的字典，若格式不符或解析失敗則拋出例外
    """
    if not raw_text:
        raise ValueError("API 回傳了空的內容")
        
    cleaned_text = raw_text.strip()
    
    # 尋找第一個 '{' 和最後一個 '}' 的位置以進行字串擷取
    # 這能有效移除 ```json ... ``` 標籤以及模型可能附帶的前後贅字
    start_idx = cleaned_text.find("{")
    end_idx = cleaned_text.rfind("}")
    
    if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
        raise ValueError("回傳文字中找不到合法的 JSON 區間")
        
    # 擷取 JSON 子字串並解析
    json_str = cleaned_text[start_idx:end_idx + 1]
    data = json.loads(json_str)
    
    # 驗證必要欄位是否存在
    required_keys = ["sentiment", "confidence", "summary"]
    for key in required_keys:
        if key not in data:
            raise KeyError(f"JSON 缺少必要欄位: {key}")
            
    # 驗證 sentiment 欄位的值是否合法
    if data["sentiment"] not in ["positive", "neutral", "negative"]:
        raise ValueError(f"不合法的 sentiment 值: {data['sentiment']}")
        
    # 驗證 confidence 欄位是否為 0~100 的整數
    try:
        data["confidence"] = int(data["confidence"])
    except (TypeError, ValueError):
        raise TypeError("confidence 欄位必須能轉換為整數")
        
    if not (0 <= data["confidence"] <= 100):
        raise ValueError(f"confidence 超出範圍 (0-100): {data['confidence']}")
        
    # 驗證 summary 欄位是否為字串
    if not isinstance(data["summary"], str):
        raise TypeError("summary 欄位必須為字串")
        
    return data


@st.cache_data(ttl=3600)
def analyze_sentiment(news_text: str) -> dict:
    """
    分析單一則新聞的情緒與摘要。
    
    使用 OpenAI API 來進行情緒判斷，並將結果解析為特定格式的字典。
    本函式已使用 Streamlit 的快取機制，相同新聞文字在 1 小時 (3600 秒) 內不會重複呼叫 API，
    以達到節省成本與防範重複請求之目的。
    
    參數:
        news_text (str): 待分析的新聞文字內容
        
    回傳:
        dict: 格式剛好為:
            {
                "sentiment": "positive" 或 "neutral" 或 "negative",
                "confidence": 0~100 的整數,
                "summary": "繁體中文的一句話摘要"
            }
            若遭遇任何網路請求失敗、API 報錯或 JSON 解析錯誤，會回傳安全的預設中性字典。
    """
    # 預設失敗回傳格式 (當 API 斷線、金鑰錯誤或 JSON 損毀時使用，防範程式崩潰)
    fallback_result = {
        "sentiment": "neutral",
        "confidence": 0,
        "summary": "分析失敗，請稍後再試"
    }
    
    # 檢查輸入值是否為空或不合法的型別
    if not news_text or not isinstance(news_text, str) or not news_text.strip():
        return fallback_result

    try:
        # 從 st.secrets 中讀取 API 金鑰 (安全第一，不寫死金鑰)
        api_key = st.secrets["OPENAI_API_KEY"]
        
        raw_response = ""
        
        # 呼叫 OpenAI API，同時相容新版 (v1.0.0+) 與舊版 (v0.x) SDK 語法
        try:
            # 嘗試使用新版 SDK (v1.0.0+)
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": news_text}
                ],
                temperature=0.0
            )
            raw_response = completion.choices[0].message.content
        except (ImportError, AttributeError):
            # 降級使用舊版 SDK (v0.x)
            import openai
            openai.api_key = api_key
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": news_text}
                ],
                temperature=0.0
            )
            raw_response = completion.choices[0].message["content"]
            
        # 清理並解析得到的原始 JSON 字串
        parsed_data = _clean_and_parse_json(raw_response)
        return parsed_data
        
    except Exception as e:
        # 穩定性鐵則：所有對外請求與解析若出錯，一律不對外丟出例外，安靜回傳預設中性字典
        # （開發期間可利用 print 或 logging 做紀錄，但對外需維持穩定性）
        return fallback_result
