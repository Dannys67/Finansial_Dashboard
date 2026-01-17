@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title T-Bank Dashboard 
color 0A

echo 🚀 T-Bank Fin_Dashboard 
echo ==========================================

set PROJECT_DIR=%~dp0T-Bank_Deploy
if exist "%PROJECT_DIR%" rmdir /s /q "%PROJECT_DIR%" 2>nul
mkdir "%PROJECT_DIR%" && cd /d "%PROJECT_DIR%"
echo [1/7] 📁 Создано: %PROJECT_DIR%

echo [2/7] 📥 GitHub tb_dashboard...
git clone -b tb_dashboard https://github.com/Dannys67/Finansial_Dashboard.git .
echo [✓] Репозиторий скачан!

echo [3/7] 🔧 t_tech.invest whl...
if not exist wheels mkdir wheels
powershell -Command "Invoke-WebRequest -Uri 'https://files.pythonhosted.org/packages/89/41/ca4f7b8985c74035744313af8af999d82e5793f8f3fc676b7580dadc9653/t_tech_investments-0.3.3-py3-none-any.whl' -OutFile './wheels/t_tech_investments-0.3.3-py3-none-any.whl'"
echo [✓] whl скачан (85kb)!

echo [4/7] 🐍 venv...
python -m venv venv && call venv\Scripts\activate.bat
echo [✓] venv активировано!

echo [5/7] 📦 Зависимости...
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
echo [✓] streamlit + t_tech + telegram-bot!

echo [6/7] 🔑 .env...
if not exist .env (
    echo TOKEN=your_tinvest_token > .env
    echo BROKER_ACCOUNT_ID=2075319459 >> .env
    echo TELEGRAM_BOT_TOKEN=your_bot_token >> .env
    start notepad .env
    echo [INFO] Отредактируйте .env (токены)!
)

echo [7/7] ✅ Готово! %PROJECT_DIR%
echo.
echo 🎯 ЛАУНЧ:
echo [1] Дашборд (localhost:8501 - 8 позиций!)
echo [2] Telegram Bot (/portfolio /balance)
echo [3] Оба
echo [0] Выход
choice /c 1230 /n /m "Выбор [1/2/3/0]: "

if %errorlevel%==4 exit /b
if %errorlevel%==3 goto both
if %errorlevel%==2 goto bot
if %errorlevel%==1 goto dashboard

:dashboard
echo [🚀] Streamlit Dashboard...
start http://localhost:8501
streamlit run dashboard.py
goto end

:bot
echo [🤖] Telegram Bot...
python telegram_bot.py
goto end

:both
echo [🚀🤖] Запуск обоих...
start /b python telegram_bot.py
timeout /t 3 >nul
start http://localhost:8501
streamlit run dashboard.py
goto end

:end
echo [INFO] Нажмите любую клавишу...
pause >nul
