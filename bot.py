import json
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, ContextTypes, filters
from flask import Flask
from threading import Thread
import os

# --------- التوكن ---------
BOT_TOKEN = os.environ.get("BOT_TOKEN") or "8471837985:AAHLOOeDL56wVRNK_EbDhnV9wjjQQkAsnvo"

# --------- مراحل ---------
CHOOSING, NUMBER, PASSWORD = range(3)
selected_action = {}

# --------- Flask سيرفر صغير ---------
app_server = Flask('')

@app_server.route('/')
def home():
    return "Bot is running ✅"

def run_server():
    app_server.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_server)
    t.start()

keep_alive()  # تشغيل السيرفر مع البوت

# --------- بداية البوت ---------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("خصم Flex 260", callback_data='flex260')],
        [InlineKeyboardButton("خصم Flex 300", callback_data='flex300')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختر نوع الخصم:", reply_markup=reply_markup)
    return CHOOSING

# --------- اختيار الزر ---------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    selected_action[user_id] = query.data
    await query.message.reply_text("تمام! ادخل رقمك:")
    return NUMBER

# --------- إدخال الرقم ---------
async def get_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['number'] = update.message.text
    await update.message.reply_text("تمام، دلوقتي ادخل الباسورد:")
    return PASSWORD

# --------- إدخال الباسورد وتنفيذ العملية ---------
async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text
    number = context.user_data['number']
    user_id = update.message.from_user.id
    action = selected_action.get(user_id)

    # ---- توكن ----
    url_token = "https://mobile.vodafone.com.eg/auth/realms/vf-realm/protocol/openid-connect/token"
    payload_token = {
        'grant_type': "password",
        'username': number,
        'password': password,
        'client_secret': "95fd95fb-7489-4958-8ae6-d31a525cd20a",
        'client_id': "ana-vodafone-app"
    }
    headers_token = {
        'User-Agent': "okhttp/4.11.0",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "gzip",
        'silentLogin': "false",
        'x-agent-operatingsystem': "13",
        'clientId': "AnaVodafoneAndroid",
        'Accept-Language': "ar",
        'x-agent-device': "Xiaomi 21061119AG",
        'x-agent-version': "2024.12.1",
        'x-agent-build': "946",
        'digitalId': "28RI9U7IINOOB"
    }

    response = requests.post(url_token, data=payload_token, headers=headers_token)
    try:
        tok = response.json()['access_token']
    except:
        await update.message.reply_text('رقمك أو الباسورد خطأ ❌')
        return ConversationHandler.END

    # ---- تحديد العملية حسب الزر ----
    if action == 'flex260':
        url_order = "https://mobile.vodafone.com.eg/services/dxl/pom/productOrder"
        payload_order = {
            # ... نفس البيانات السابقة لـ flex260 ...
        }
    elif action == 'flex300':
        url_order = "https://mobile.vodafone.com.eg/services/dxl/pom/productOrder"
        payload_order = {
            # ... نفس البيانات السابقة لـ flex300 ...
        }
    else:
        await update.message.reply_text("حدث خطأ، الرجاء إعادة المحاولة ❌")
        return ConversationHandler.END

    headers_order = {
        'User-Agent': "okhttp/4.11.0",
        'Connection': "Keep-Alive",
        'Accept': "application/json",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/json",
        'Authorization': f"Bearer {tok}",
        'api-version': "v2",
        'x-agent-operatingsystem': "13",
        'clientId': "AnaVodafoneAndroid",
        'x-agent-device': "Xiaomi 21061119AG",
        'x-agent-version': "2024.12.1",
        'x-agent-build': "946",
        'msisdn': number,
        'Accept-Language': "ar",
        'Content-Type': "application/json; charset=UTF-8"
    }

    response = requests.post(url_order, data=json.dumps(payload_order), headers=headers_order)
    try:
        foxxx = response.json()['reason']
        if foxxx == "Success With Grace":
            await update.message.reply_text(f'تم تفعيل {action} ✅')
        else:
            await update.message.reply_text(f'النتيجة: {foxxx}')
    except:
        await update.message.reply_text(f'حدث خطأ:\n{response.text}')

    return ConversationHandler.END

# --------- إلغاء العملية ---------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم إلغاء العملية ❌")
    return ConversationHandler.END

# --------- إعداد البوت ---------
app = ApplicationBuilder().token(BOT_TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        CHOOSING: [CallbackQueryHandler(button)],
        NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_number)],
        PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

app.add_handler(conv_handler)

print("البوت شغال... اضغط CTRL+C للإيقاف")
app.run_polling()