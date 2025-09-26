import json
import requests
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)

# --------- توكن البوت ---------
BOT_TOKEN = "8471837985:AAHLOOeDL56wVRNK_EbDhnV9wjjQQkAsnvo"

# --------- مراحل ---------
CHOOSING, NUMBER, PASSWORD = range(3)
selected_action = {}

# --------- Flask سيرفر صغير للـKeep-Alive ---------
app_server = Flask('')

@app_server.route('/')
def home():
    return "Bot is running ✅"

def run_server():
    app_server.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_server)
    t.start()

keep_alive()

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
    number = context.user_data.get('number')
    user_id = update.message.from_user.id
    action = selected_action.get(user_id)

    if not number:
        await update.message.reply_text("مفيش رقم محفوظ، ابعت الرقم تاني.")
        return ConversationHandler.END

    session = requests.Session()

    # ---- طلب التوكن ----
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
        'Content-Type': "application/x-www-form-urlencoded",
        'silentLogin': "false",
        'x-agent-operatingsystem': "13",
        'clientId': "AnaVodafoneAndroid",
        'Accept-Language': "ar",
        'x-agent-device': "Xiaomi 21061119AG",
        'x-agent-version': "2024.12.1",
        'x-agent-build': "946",
        'digitalId': "28RI9U7IINOOB"
    }

    try:
        resp_token = session.post(url_token, data=payload_token, headers=headers_token, timeout=15)
    except Exception as e:
        await update.message.reply_text(f'حصل خطأ في الاتصال بالـAuth:\n{e}')
        return ConversationHandler.END

    if resp_token.status_code != 200:
        await update.message.reply_text(f'خطأ {resp_token.status_code} في الحصول على التوكن:\n{resp_token.text[:1000]}')
        return ConversationHandler.END

    try:
        tok = resp_token.json().get('access_token')
    except:
        await update.message.reply_text(f'الـAPI رجع حاجة مش JSON:\n{resp_token.text[:1500]}')
        return ConversationHandler.END

    if not tok:
        await update.message.reply_text(f'فشل الحصول على التوكن:\n{resp_token.json()}')
        return ConversationHandler.END

    # ---- تحديد payload حسب الزر ----
    if action == 'flex260':
        url_order = "https://mobile.vodafone.com.eg/services/dxl/pom/productOrder"
        payload_order = {
            "channel": {"name": "MobileApp"},
            "orderItem": [
                {
                    "action": "add",
                    "id": "Flex_2021_523",
                    "itemPrice": [
                        {"name": "OriginalPrice", "price": {"taxIncludedAmount": {"unit": "LE", "value": "130.0"}}},
                        {"name": "MigrationFees", "price": {"taxIncludedAmount": {"unit": "LE", "value": "0.0"}}}
                    ],
                    "product": {
                        "characteristic": [
                            {"name": "offerRank", "value": "1"},
                            {"name": "TariffID", "value": "523"},
                            {"name": "Quota"},
                            {"name": "Validity", "@type": "MONTH", "value": "1"},
                            {"name": "MaxAdjustmentNumber", "value": "1"},
                            {"name": "TariffRank", "value": "6"},
                            {"name": "MigrationDesc", "value": "Intervention Offer Migration"},
                            {"name": "CohortId", "value": "24"}
                        ],
                        "productSpecification": [
                            {"id": "Retention With Offer", "name": "Category"},
                            {"id": "Upon Renewal / Repurchase", "name": "MigrationRule"},
                            {"id": "10", "name": "RatePlanType"},
                            {"id": "Flex Family", "name": "BundleType"}
                        ],
                        "relatedParty": [
                            {"id": number, "name": "MSISDN", "@referredType": "prepaid", "role": "Subscriber"},
                            {"id": "523", "name": "TariffID", "@referredType": "prepaid", "role": "TariffID"}
                        ]
                    },
                    "@type": "Access fees Discount",
                    "eCode": 0
                }
            ],
            "@type": "InterventionTariff"
        }

    elif action == 'flex300':
        url_order = "https://mobile.vodafone.com.eg/services/dxl/pom/productOrder"
        payload_order = {
            "channel": {"name": "MobileApp"},
            "orderItem": [
                {
                    "action": "add",
                    "id": "Flex_2024_633",
                    "itemPrice": [
                        {"name": "OriginalPrice", "price": {"taxIncludedAmount": {"unit": "", "value": "150.0"}}},
                        {"name": "MigrationFees", "price": {"taxIncludedAmount": {"unit": "LE", "value": "0.0"}}}
                    ],
                    "product": {
                        "characteristic": [
                            {"name": "TariffRank", "value": "2"},
                            {"name": "TariffID", "value": "633"},
                            {"name": "Quota"},
                            {"name": "Validity"},
                            {"name": "MaxAdjustmentNumber", "value": ""},
                            {"name": "offerRank", "value": "1"},
                            {"name": "MigrationDesc", "value": "Intervention Offer Migration"},
                            {"name": "CohortId", "value": "11"}
                        ],
                        "productSpecification": [
                            {"id": "Migrations", "name": "Category"},
                            {"id": "Upon Migration", "name": "MigrationRule"},
                            {"id": "0", "name": "RatePlanType"},
                            {"id": "Flex Family", "name": "BundleType"}
                        ],
                        "relatedParty": [
                            {"id": number, "name": "MSISDN", "@referredType": "prepaid", "role": "Subscriber"},
                            {"id": "470", "name": "TariffID", "@referredType": "prepaid", "role": "TariffID"}
                        ]
                    },
                    "@type": "Migration Fees",
                    "eCode": 0
                }
            ],
            "@type": "InterventionTariff"
        }

    else:
        await update.message.reply_text("حدث خطأ، الرجاء إعادة المحاولة ❌")
        return ConversationHandler.END

    headers_order = {
        'User-Agent': "okhttp/4.11.0",
        'Connection': "Keep-Alive",
        'Accept': "application/json",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/json; charset=UTF-8",
        'Authorization': f"Bearer {tok}",
        'api-version': "v2",
        'x-agent-operatingsystem': "13",
        'clientId': "AnaVodafoneAndroid",
        'x-agent-device': "Xiaomi 21061119AG",
        'x-agent-version': "2024.12.1",
        'x-agent-build': "946",
        'msisdn': number,
        'Accept-Language': "ar"
    }

    try:
        resp_order = session.post(url_order, data=json.dumps(payload_order), headers=headers_order, timeout=15)
        foxxx = resp_order.json().get('reason')
        if foxxx == "Success With Grace":
            await update.message.reply_text(f'تم تفعيل {action} ✅')
        else:
            await update.message.reply_text(f'النتيجة: {foxxx}')
    except Exception as e:
        await update.message.reply_text(f'حدث خطأ:\n{resp_order.text[:1500]}')

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