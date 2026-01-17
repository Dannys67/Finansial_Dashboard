#!/usr/bin/env python3

import os
import logging
from typing import Optional

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
from t_tech.invest import Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
TINVEST_TOKEN = os.getenv("TOKEN")
ACCOUNT_ID = os.getenv("BROKER_ACCOUNT_ID")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not all([TINVEST_TOKEN, ACCOUNT_ID, BOT_TOKEN]):
    raise ValueError("❌ .env: TOKEN, BROKER_ACCOUNT_ID, TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Стартовое сообщение."""
    await update.message.reply_text(
        "🚀 T‑Bank ФинБот\n\n"
        "/portfolio - портфель (топ-8)\n"
        "/balance - баланс + НКД\n"
        "/pnl - топ-5 PnL\n"
        "/top - топ по стоимости",
        parse_mode='HTML'
    )

async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Топ-8 позиций портфеля."""
    try:
        with Client(TINVEST_TOKEN) as client:
            pf = client.operations.get_portfolio(account_id=ACCOUNT_ID)
        
        total_cost = 0
        msg = f"📊 Портфель ({len(pf.positions)} позиций)\n\n"
        
        for pos in pf.positions[:8]:
            ticker = getattr(pos, 'ticker', 'RUB') or 'RUB'
            qty = getattr(pos.quantity, 'units', 0) if pos.quantity else 0
            price_units = getattr(pos.current_price, 'units', 0) if pos.current_price else 0
            pnl = getattr(pos.expected_yield, 'units', 0) if pos.expected_yield else 0
            
            price = f"{price_units}.{getattr(pos.current_price, 'nano', 0)//10**8:02d}"
            cost = qty * price_units
            total_cost += cost
            
            msg += f"{ticker}: {qty}л @ {price}₽ | PnL {pnl:+,}₽\n"
        
        msg += f"\n💰 Примерная стоимость: ~{total_cost:,.0f}₽"
        await update.message.reply_text(msg, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Portfolio error: {e}")
        await update.message.reply_text(f"❌ {e}")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Баланс с НКД."""
    try:
        with Client(TINVEST_TOKEN) as client:
            pf = client.operations.get_portfolio(account_id=ACCOUNT_ID)
        
        # Сумма НКД по позициям (безопасно)
        total_nkd = 0
        for pos in pf.positions:
            nkd = getattr(pos.current_nkd, 'units', 0) if pos.current_nkd else 0
            total_nkd += nkd
        
        msg = f"💳 Баланс счета\n\n"
        msg += f"📈 Стоимость портфеля (с НКД): ~{total_nkd:,}₽\n"
        msg += f"📊 Позиций: {len(pf.positions)}"
        
        await update.message.reply_text(msg, parse_mode='HTML')
        
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")

async def pnl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Топ-5 по PnL."""
    try:
        with Client(TINVEST_TOKEN) as client:
            pf = client.operations.get_portfolio(account_id=ACCOUNT_ID)
        
        top = sorted(
            pf.positions, 
            key=lambda p: getattr(p.expected_yield, 'units', 0) if p.expected_yield else 0, 
            reverse=True
        )[:5]
        
        msg = "📈 ТОП-5 PnL:\n\n"
        for pos in top:
            ticker = getattr(pos, 'ticker', '?')
            pnl_val = getattr(pos.expected_yield, 'units', 0)
            msg += f"{ticker}: {pnl_val:+,}₽\n"
        
        await update.message.reply_text(msg, parse_mode='HTML')
        
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Топ по стоимости."""
    try:
        with Client(TINVEST_TOKEN) as client:
            pf = client.operations.get_portfolio(account_id=ACCOUNT_ID)
        
        top = sorted(
            pf.positions,
            key=lambda p: (getattr(p.current_price, 'units', 0) * 
                          getattr(p.quantity, 'units', 0) if p.current_price and p.quantity 
                          else 0),
            reverse=True
        )[:5]
        
        msg = "💎 ТОП-5 по стоимости:\n\n"
        for pos in top:
            ticker = getattr(pos, 'ticker', '?')
            qty = getattr(pos.quantity, 'units', 0)
            price = getattr(pos.current_price, 'units', 0)
            cost = qty * price
            msg += f"{ticker}: {cost:,.0f}₽ ({qty}л)\n"
        
        await update.message.reply_text(msg, parse_mode='HTML')
        
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("portfolio", portfolio))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("pnl", pnl))
    app.add_handler(CommandHandler("top", top))
    
    logger.info("🤖 T-Bank Bot запущен")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
