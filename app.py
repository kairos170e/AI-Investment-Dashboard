"""前端主程式入口 —— 負責人：許德禎
這是「可以跑的骨架」，已串好所有模組的呼叫流程。
TODO（許德禎）：請美化版面與互動。
★ 其他人請只改自己的模組，不要更動這裡 import 的函式名稱與用法。
"""
import streamlit as st
import plotly.graph_objects as go

from database_manager import add_ticker, get_watchlist, remove_ticker
from data_fetcher import get_stock_data, get_news
from indicators import add_indicators
from ai_analyzer import analyze_sentiment

st.set_page_config(page_title="量化投資儀表板", layout="wide")
st.title("📈 智慧量化投資與市場分析儀表板（骨架版）")

# --- 用 session_state 記住目前選取的股票（Streamlit 每次互動都會重跑，普通變數會被歸零）---
if "selected" not in st.session_state:
    st.session_state.selected = None

# --- 側邊欄：自選股 CRUD ---
with st.sidebar:
    st.header("我的自選股")
    new_ticker = st.text_input("輸入股票代碼（如 2330.TW、AAPL）")
    if st.button("新增"):
        if add_ticker(new_ticker):
            st.success(f"已新增 {new_ticker}")
        else:
            st.warning("代碼為空或已存在")

    watchlist = get_watchlist()
    if not watchlist:
        st.info("清單是空的，請先新增股票")
    for tk in watchlist:
        col_pick, col_del = st.columns([3, 1])
        if col_pick.button(tk, key=f"sel_{tk}"):
            st.session_state.selected = tk
        if col_del.button("刪除", key=f"del_{tk}"):
            remove_ticker(tk)
            st.rerun()

# --- 主畫面 ---
ticker = st.session_state.selected
if not ticker:
    st.info("請從左側點選一檔股票")
    st.stop()

st.subheader(f"標的：{ticker}")

# 1) 取股價 → 算指標
df = get_stock_data(ticker)
if df.empty:
    st.warning("目前無法取得該標的數據，請稍後再試")
    st.stop()
df = add_indicators(df)

# 2) 畫 K 線
fig = go.Figure(
    data=[
        go.Candlestick(
            x=df.index,
            open=df["Open"], high=df["High"],
            low=df["Low"], close=df["Close"],
            name="K線",
        )
    ]
)
# 指標若已算出（非全為 NaN）就疊上去
if "SMA_20" in df.columns and df["SMA_20"].notna().any():
    fig.add_trace(go.Scatter(x=df.index, y=df["SMA_20"], name="SMA_20"))
fig.update_layout(xaxis_rangeslider_visible=False, height=500)
st.plotly_chart(fig, use_container_width=True)

# 3) 新聞 + 情緒分析
st.subheader("相關新聞與情緒分析")
news = get_news(ticker)
if not news:
    st.info("目前沒有相關新聞")
for item in news:
    result = analyze_sentiment(item["title"])
    icon = {"positive": "🟢", "neutral": "⚪", "negative": "🔴"}.get(result["sentiment"], "⚪")
    st.markdown(f"{icon} **{item['title']}**　信心 {result['confidence']}/100")
    st.caption(result["summary"])
