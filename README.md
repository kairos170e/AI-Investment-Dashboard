# 智慧量化投資與市場分析儀表板

5 人 Vibe Coding 團隊專案。完整開發規範見《AI協作開發規範》文件。

## 快速開始
1. clone 專案
2. `pip install -r requirements.txt`
3. 建立 `.streamlit/secrets.toml`（見下方），填入金鑰
4. `streamlit run app.py`

## 金鑰設定
在專案根目錄建立 `.streamlit/secrets.toml`（此檔已被 .gitignore，不會上傳）：

```toml
OPENAI_API_KEY = "你的金鑰"
NEWS_API_KEY = "你的金鑰"
```

部署到 Streamlit Community Cloud 時，金鑰改在 Cloud 後台的 Secrets 介面設定（格式相同）。

## 檔案分工
| 檔案 | 負責人 |
|---|---|
| app.py | 許德禎（前端） |
| database_manager.py | 徐宏智（CRUD） |
| data_fetcher.py | 徐宏智（股價 / 新聞） |
| indicators.py | 王仱婕（指標） |
| ai_analyzer.py | 呂昇峰（情緒分析） |
| requirements.txt / .gitignore / 部署 | 林玄晉 |

## 鐵則
- **不要改別人函式的名稱與回傳格式**（見介面契約）。
- 各模組對外請求都要 `try-except` + 回傳安全預設值。
- 金鑰一律用 `st.secrets`，禁止寫死在程式碼裡。

## 目前狀態
**骨架版**：所有模組目前是「臨時假資料」，畫面已經可以跑起來。
各負責人把自己模組的 `TODO` 換成真實邏輯即可，函式介面維持不變。
