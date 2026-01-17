#!/usr/bin/env python3

import os
import logging
from typing import Optional, List

import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from t_tech.invest import Client, MoneyValue

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.getenv("TOKEN")
ACCOUNT_ID = os.getenv("BROKER_ACCOUNT_ID")

if not TOKEN:
    st.error("❌ TOKEN не найден в .env")
    st.stop()

st.set_page_config(page_title="T-Bank Dashboard", page_icon="🚀", layout="wide")

@st.cache_data(ttl=300, show_spinner="📊 Загрузка портфеля...")
def get_portfolio():
    try:
        with Client(TOKEN) as client:
            return client.operations.get_portfolio(account_id=ACCOUNT_ID)
    except Exception as e:
        st.error(f"❌ API: {e}")
        return None

def format_price(money: Optional[MoneyValue]) -> str:
    if not money or money.units == 0:
        return "0 ₽"
    nano = getattr(money, 'nano', 0) // 100_000_000
    return f"{money.units:,}.{nano:02d} ₽"

def format_quantity(qty) -> str:
    units = getattr(qty, 'units', 0) if qty else 0
    return f"{units:,} лотов" if units else "0"

def calculate_portfolio_value(positions: List) -> tuple[int, int]:
    """Расчёт общей стоимости и НКД из позиций."""
    total_value = total_nkd = 0
    for pos in positions:
        # Стоимость позиции
        price = getattr(pos.current_price, 'units', 0) if pos.current_price else 0
        qty_units = getattr(pos.quantity, 'units', 0) if pos.quantity else 0
        total_value += price * qty_units
        
        # НКД позиции
        nkd = getattr(pos.current_nkd, 'units', 0) if pos.current_nkd else 0
        total_nkd += nkd
    return total_value, total_nkd

# Главная страница
st.title("🚀 T-Bank Портфель")

portfolio = get_portfolio()
if not portfolio or not hasattr(portfolio, 'positions'):
    st.stop()

positions = portfolio.positions
data, total_pnl, total_day = [], 0, 0

for pos in positions:
    pnl_abs = getattr(getattr(pos, 'expected_yield', None), 'units', 0)
    day_pnl = getattr(getattr(pos, 'daily_yield', None), 'units', 0)
    
    total_pnl += pnl_abs
    total_day += day_pnl
    
    data.append({
        'Тикер': getattr(pos, 'ticker', '—'),
        'FIGI': getattr(pos, 'figi', '—'),
        'Лотов': format_quantity(getattr(pos, 'quantity', None)),
        'Текущая': format_price(getattr(pos, 'current_price', None)),
        'PnL, ₽': f"{pnl_abs:+,} ₽",
        'День, ₽': f"{day_pnl:+,} ₽",
        'НКД': format_price(getattr(pos, 'current_nkd', None))
    })

df = pd.DataFrame(data)
st.dataframe(df, use_container_width=True, hide_index=True)

# Метрики
col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("📊 Позиций", len(df))
with col2: st.metric("💰 PnL", f"{total_pnl:+,} ₽")
with col3: st.metric("📅 День", f"{total_day:+,} ₽")

# ✅ Фикс: Сумма по позициям вместо portfolio.total
portfolio_value, total_nkd = calculate_portfolio_value(positions)
with col4:
    st.metric("💵 Стоимость", f"{portfolio_value:,} ₽")

st.metric("🎟️ Суммарный НКД", f"{total_nkd:,} ₽")

st.success(f"✅ {len(positions)} позиций | +{total_pnl:,}₽ PnL")
st.caption("🔄 5 мин | Rainway: --server.port 3000")
