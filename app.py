# app.py — 智慧量化投資與市場分析儀表板（前端主程式入口）
# 負責人：許德禎
# 鐵則：只 import 隊友模組來「呼叫」，絕不重寫；所有跨互動的狀態用 st.session_state；
#       任何對外抓回來是空的（df.empty / news == []）都用 st.warning 友善提示，不讓畫面崩潰。

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# === 匯入隊友模組（介面契約鎖死，只能呼叫不可修改）===
from database_manager import add_ticker, get_watchlist, remove_ticker  # 徐宏智
from data_fetcher import get_stock_data, get_news                       # 徐宏智
from indicators import add_indicators                                   # 王仱婕
from ai_analyzer import analyze_sentiment                               # 呂昇峰

# === 頁面基本設定（寬版佈局）===
st.set_page_config(page_title="量化投資儀表板", page_icon="📊", layout="wide")

# === session_state 初始化：記住目前選取的股票（Streamlit 每次互動會重跑整個檔案）===
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = None


# ------------------------------------------------------------------
# 工具函式
# ------------------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner=False)
def cached_sentiment(news_text: str) -> dict:
    """把 analyze_sentiment 的結果快取 1 小時。
    目的：同一則新聞文字不必每次 rerun 都重打一次 LLM，省 token 也更快。
    這只是「包一層快取」，不改變回傳格式（仍是 {sentiment, confidence, summary}）。"""
    return analyze_sentiment(news_text)


def render_main_chart(df, ticker):
    """畫 K 線 + 均線 + RSI + MACD 的三層分圖。傳入的 df 需已經過 add_indicators()。"""
    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=("K 線 & 均線", "RSI (14)", "MACD"),
    )

    # 第 1 層：K 線（台股習慣紅漲綠跌；若要做美股可把下面兩個顏色對調）
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"], name="K 線",
        increasing_line_color="#ef4444", decreasing_line_color="#22c55e",
    ), row=1, col=1)

    # 疊均線（資料筆數不足時這些欄位會是 NaN，plotly 會自動略過、不會壞）
    for col, color in [("SMA_20", "#f59e0b"), ("SMA_60", "#3b82f6")]:
        if col in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df[col], name=col,
                          line=dict(width=1.2, color=color)), row=1, col=1)

    # 第 2 層：RSI + 70/30 超買超賣參考線
    if "RSI_14" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["RSI_14"], name="RSI",
                      line=dict(width=1.2, color="#8b5cf6")), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#22c55e", row=2, col=1)

    # 第 3 層：MACD 柱狀圖（紅綠）+ 快慢線
    if "MACDh_12_26_9" in df.columns:
        bar_colors = ["#ef4444" if v >= 0 else "#22c55e" for v in df["MACDh_12_26_9"]]
        fig.add_trace(go.Bar(x=df.index, y=df["MACDh_12_26_9"], name="MACD 柱",
                      marker_color=bar_colors), row=3, col=1)
    if "MACD_12_26_9" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["MACD_12_26_9"], name="MACD",
                      line=dict(width=1, color="#3b82f6")), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["MACDs_12_26_9"], name="Signal",
                      line=dict(width=1, color="#f59e0b")), row=3, col=1)

    fig.update_layout(
        height=720,
        xaxis_rangeslider_visible=False,  # ★ 分圖一定要關掉預設拖曳條，否則版面會被擠歪
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig


# sentiment 字串 → (燈號 emoji, 中文標籤) 對照表
SENTIMENT_UI = {
    "positive": ("🟢", "利多"),
    "neutral":  ("⚪", "中性"),
    "negative": ("🔴", "利空"),
}


# ------------------------------------------------------------------
# 側邊欄：自選股管理（新增 / 顯示 / 選取 / 刪除）
# ------------------------------------------------------------------

with st.sidebar:
    st.header("📋 自選股清單")

    # --- 新增區：輸入框 + 按鈕（呼叫 add_ticker）---
    new_ticker = st.text_input("輸入股票代碼", placeholder="例如 2330.TW 或 AAPL")
    if st.button("➕ 加入自選股", use_container_width=True):
        code = new_ticker.strip().upper()
        if not code:
            st.warning("請先輸入股票代碼")
        elif add_ticker(code):                       # 成功新增 → True
            st.session_state.selected_ticker = code  # 順手切換為目前分析標的
            st.success(f"已加入 {code}")
            st.rerun()
        else:                                        # 已存在或空值 → False
            st.info(f"{code} 已在清單中（或代碼無效）")

    st.divider()

    # --- 清單區：固定高度容器，清單再長也只佔這塊、可自行捲動 ---
    watchlist = get_watchlist()  # 回傳 list[str]，沒資料回 []
    if not watchlist:
        st.caption("清單是空的，先在上面加一檔吧。")
    else:
        with st.container(height=300):
            for tk in watchlist:
                col_pick, col_del = st.columns([4, 1])
                # 目前選取的那一檔用 primary 樣式標起來，一眼看得出在分析哪檔
                btn_type = "primary" if tk == st.session_state.selected_ticker else "secondary"
                if col_pick.button(tk, key=f"pick_{tk}",
                                   use_container_width=True, type=btn_type):
                    st.session_state.selected_ticker = tk
                    st.rerun()
                # 點 ✕ → 從清單移除（呼叫 remove_ticker）
                if col_del.button("✕", key=f"del_{tk}"):
                    remove_ticker(tk)
                    # 若刪掉的剛好是目前選取的，清掉選取狀態避免主畫面找不到資料
                    if st.session_state.selected_ticker == tk:
                        st.session_state.selected_ticker = None
                    st.rerun()


# ------------------------------------------------------------------
# 主畫面
# ------------------------------------------------------------------

st.title("📊 智慧量化投資與市場分析儀表板")

ticker = st.session_state.selected_ticker

# 防呆 1：還沒選股票 → 提示後直接停在這裡，不往下渲染
if not ticker:
    st.info("👈 請從左側自選股清單點選一檔股票開始分析。")
    st.stop()

st.subheader(f"目前標的：{ticker}")

# 抓行情 + 算指標（用 spinner 給等待回饋）
with st.spinner(f"正在抓取並計算 {ticker} 的行情…"):
    df = get_stock_data(ticker)        # 失敗會回空 DataFrame（契約規定不會回 None）
    if not df.empty:
        df = add_indicators(df)        # 加上 SMA/RSI/MACD 等欄位

# 防呆 2：抓不到資料
if df.empty:
    st.warning(f"查無 {ticker} 的資料，請確認代碼是否正確（台股記得加 .TW，例如 2330.TW）。")
    st.stop()

# --- 數據卡片（含當日漲跌幅）---
latest = df.iloc[-1]
prev = df.iloc[-2] if len(df) >= 2 else latest
change = latest["Close"] - prev["Close"]
pct = (change / prev["Close"] * 100) if prev["Close"] else 0
c1, c2, c3 = st.columns(3)
c1.metric("收盤價", f"{latest['Close']:.2f}", f"{change:+.2f} ({pct:+.2f}%)",
          delta_color="inverse")  # 台股紅漲綠跌；若主要做美股，把這個參數整行拿掉即可
c2.metric("最高價", f"{latest['High']:.2f}")
c3.metric("成交量", f"{latest['Volume']:,.0f}")

# --- 分頁：技術分析 / 新聞情緒 ---
tab_chart, tab_news = st.tabs(["📈 技術分析", "📰 新聞情緒"])

with tab_chart:
    st.plotly_chart(render_main_chart(df, ticker), use_container_width=True)

with tab_news:
    # 台股代碼帶 .TW 抓新聞命中率低，去掉後綴只用數字/英文代碼當關鍵字
    news_query = ticker.split(".")[0]
    with st.spinner("正在抓取並分析新聞情緒…"):
        news_list = get_news(news_query)   # 失敗或無資料回 []

    # 防呆 3：沒新聞
    if not news_list:
        st.warning("目前抓不到這檔的相關新聞。")
    else:
        # 先逐則做情緒分析，順便統計整體分布
        results = []
        counter = {"positive": 0, "neutral": 0, "negative": 0}
        for item in news_list:
            text = f"{item.get('title', '')}。{item.get('description', '')}"
            res = cached_sentiment(text)  # 回傳 {sentiment, confidence(0~100), summary}
            results.append((item, res))
            counter[res.get("sentiment", "neutral")] += 1

        # 整體情緒總覽
        m1, m2, m3 = st.columns(3)
        m1.metric("🟢 利多", counter["positive"])
        m2.metric("⚪ 中性", counter["neutral"])
        m3.metric("🔴 利空", counter["negative"])
        st.divider()

        # 逐則新聞卡片
        for item, res in results:
            emoji, label = SENTIMENT_UI.get(res.get("sentiment", "neutral"), ("⚪", "中性"))
            confidence = int(res.get("confidence", 0))
            with st.container(border=True):
                head, body = st.columns([1, 5])
                with head:
                    st.markdown(f"### {emoji}")
                    st.caption(f"{label}・信心 {confidence}%")
                with body:
                    title = item.get("title", "（無標題）")
                    url = item.get("url", "")
                    st.markdown(f"**[{title}]({url})**" if url else f"**{title}**")
                    st.write(res.get("summary", ""))
                    st.caption(f"🕒 {item.get('publishedAt', '')}")
                # 信心進度條（夾在 0~100 之間再轉成 0~1）
                st.progress(min(max(confidence, 0), 100) / 100)
