# bot.py

import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# database.py से फंक्शन्स इंपोर्ट करें
from database import get_user_data, can_mine, perform_mine, get_time_left, MINE_REWARD

# .env फ़ाइल से वेरिएबल्स लोड करें (लोकल टेस्टिंग के लिए)
load_dotenv()

# --- कमांड हैंडलर्स ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """'/start' कमांड को हैंडल करता है।"""
    user_id = update.effective_user.id
    user = await get_user_data(user_id) # Firebase से डेटा लाओ
    
    if user is None:
        await update.message.reply_text("❌ डेटाबेस कनेक्शन में त्रुटि।")
        return

    welcome_message = (
        "🔥 **ChillMiner Bot में आपका स्वागत है!**\n\n"
        "आपका वर्तमान $CHILL बैलेंस: **{:.2f}**\n\n"
        "कमांड्स:\n"
        "➡️ `/mine` - माइनिंग शुरू करें ({} $CHILL)\n"
        "➡️ `/balance` - अपना वर्तमान बैलेंस देखें।"
    ).format(user['balance'], MINE_REWARD)
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')


async def mine_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """'/mine' कमांड को हैंडल करता है।"""
    user_id = update.effective_user.id
    user = await get_user_data(user_id)
    if user is None: return

    # जाँचें कि यूजर माइन कर सकता है या नहीं
    can, time_since_last_mine = await can_mine(user_id)
    
    if can:
        # माइनिंग करें, Firebase में अपडेट करें
        reward, new_balance = await perform_mine(user_id, user['balance'])
        
        success_message = (
            "⛏️ **माइनिंग सफल!**\n\n"
            "आपने सफलतापूर्वक **{:.2f} $CHILL** माइन किए हैं।\n"
            "नया बैलेंस: **{:.2f} $CHILL**\n\n"
            "अगली माइनिंग: 8 घंटे बाद।"
        ).format(reward, new_balance)
        
        await update.message.reply_text(success_message, parse_mode='Markdown')
        
    else:
        # यदि माइन नहीं कर सकते, तो बचा हुआ समय बताएं
        time_left_str = get_time_left(time_since_last_mine)
        
        wait_message = (
            "🛑 **अभी बहुत जल्दी है!**\n\n"
            "आप हर 8 घंटे में केवल एक बार माइन कर सकते हैं।\n"
            "अगली माइनिंग शुरू होने में बचा हुआ समय:\n"
            "⏳ **{}**"
        ).format(time_left_str)
        
        await update.message.reply_text(wait_message, parse_mode='Markdown')


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """'/balance' कमांड को हैंडल करता है।"""
    user_id = update.effective_user.id
    user = await get_user_data(user_id) # Firebase से डेटा लाओ
    if user is None: return

    balance_message = (
        "💰 **$CHILL बैलेंस**\n\n"
        "आपका वर्तमान $CHILL बैलेंस है: **{:.2f}**"
    ).format(user['balance'])
    
    await update.message.reply_text(balance_message, parse_mode='Markdown')


# --- मुख्य फ़ंक्शन ---

def main():
    """बॉट को शुरू करता है और कमांड हैंडलर्स को जोड़ता है।"""
    # Render Env Var या .env से टोकन प्राप्त करें
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("ERROR: BOT_TOKEN Environment Variable नहीं मिला।")
        return

    application = ApplicationBuilder().token(token).build()

    # कमांड हैंडलर्स जोड़ें
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("mine", mine_command))
    application.add_handler(CommandHandler("balance", balance_command))
    
    # बॉट को पोलिंग (polling) शुरू करने के लिए रन करें
    print("ChillMiner Bot (Production Mode) शुरू हो रहा है...")
    application.run_polling()

if __name__ == '__main__':
main()
