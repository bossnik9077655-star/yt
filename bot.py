import os
import asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import Message
from flask import Flask
from threading import Thread

# --- वेब सर्वर (Render/HuggingFace को 24/7 जगाए रखने के लिए) ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is Running Live 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# --- टेलीग्राम बॉट सेटअप ---
API_ID = 34793313
API_HASH = "9f2f3b666be702826a6da45024bf4ec7"
BOT_TOKEN = "8698411409:AAH8tP0Lvd1iml2kUJVDGg7R9CEJmNem_Vc"

app = Client("ThumbnailBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# एडमिन और डिफ़ॉल्ट सेटिंग्स
ADMIN_USERNAME = "Nikboss9"
BOT_PASSWORD = "nikhil"

# डेटाबेस (मेमोरी में)
allowed_users = set()  
waiting_for_password = set()  
user_video_cache = {}  

# --- प्रोग्रेस बार फंक्शन ---
async def progress_bar(current, total, msg, action, prev_time):
    now = time.time()
    if now - prev_time[0] > 2 or current == total:
        prev_time[0] = now
        percent = current * 100 / total
        filled = int(percent / 10)
        bar = "█" * filled + "░" * (10 - filled)
        c_mb = current / (1024 * 1024)
        t_mb = total / (1024 * 1024)
        
        text = f"⚡ **{action}**\n\n📊 प्रोग्रेस: [{bar}] {percent:.1f}%\n💾 साइज़: {c_mb:.1f} MB / {t_mb:.1f} MB"
        try:
            await msg.edit_text(text)
        except:
            pass

# --- एडमिन कमांड्स (Only for @Nikboss9) ---

@app.on_message(filters.command("add") & filters.private)
async def add_user(client, message):
    if message.from_user.username != ADMIN_USERNAME:
        return await message.reply_text("❌ यह कमांड केवल एडमिन के लिए है।")
    try:
        new_user = message.text.split(" ")[1].replace("@", "")
        allowed_users.add(new_user)
        await message.reply_text(f"✅ यूज़र @{new_user} को एक्सेस दे दिया गया है! 🚀")
    except:
        await message.reply_text("⚠️ फॉर्मेट: `/add username`")

@app.on_message(filters.command("rmv") & filters.private)
async def remove_user(client, message):
    if message.from_user.username != ADMIN_USERNAME:
        return await message.reply_text("❌ यह कमांड केवल एडमिन के लिए है।")
    try:
        rem_user = message.text.split(" ")[1].replace("@", "")
        allowed_users.discard(rem_user)
        await message.reply_text(f"✅ @{rem_user} का एक्सेस हटा दिया गया है। 🗑️")
    except:
        await message.reply_text("⚠️ फॉर्मेट: `/rmv username`")

@app.on_message(filters.command("list") & filters.private)
async def list_users(client, message):
    if message.from_user.username != ADMIN_USERNAME: return
    users_list = "\n".join([f"👤 @{u}" for u in allowed_users]) or "कोई यूज़र नहीं है।"
    await message.reply_text(f"📋 **अनुमति प्राप्त यूज़र्स की लिस्ट:**\n\n{users_list}")

@app.on_message(filters.command("change") & filters.private)
async def change_password(client, message):
    global BOT_PASSWORD
    if message.from_user.username != ADMIN_USERNAME: return
    try:
        BOT_PASSWORD = message.text.split(" ")[1]
        await message.reply_text(f"🔐 बॉट का नया पासवर्ड सेट हो गया: `{BOT_PASSWORD}`")
    except:
        await message.reply_text("⚠️ फॉर्मेट: `/change newpassword`")

# --- ग्लोबल कमांड्स ---

@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    user = message.from_user.username or message.from_user.first_name
    welcome_msg = (
        f"✨ **नमस्ते @{user}!** 👋\n\n"
        f"मैं एक **Professional Thumbnail Bot** हूँ। 🤖\n"
        f"मैं आपके वीडियो पर मनचाहा थंबनेल लगा सकता हूँ।\n\n"
        f"🛠️ मदद के लिए /help दबाएं।"
    )
    
    if user == ADMIN_USERNAME or user in allowed_users:
        await message.reply_text(f"{welcome_msg}\n\n✅ आपका एक्सेस एक्टिव है। कृपया वीडियो भेजें!")
    else:
        waiting_for_password.add(message.from_user.id)
        await message.reply_text(f"{welcome_msg}\n\n🔒 **सुरक्षा जांच:** कृपया बॉट का पासवर्ड दर्ज करें:")

@app.on_message(filters.command("help") & filters.private)
async def help_cmd(client, message):
    help_text = (
        "📖 **बॉट कैसे इस्तेमाल करें?**\n\n"
        "1️⃣ सबसे पहले एक **वीडियो** भेजें।\n"
        "2️⃣ फिर एक **फोटो** भेजें जिसे थंबनेल बनाना है।\n"
        "3️⃣ बॉट आपको थंबनेल लगा हुआ वीडियो भेज देगा! 🎉\n\n"
        "⚠️ *नोट: केवल अधिकृत यूज़र्स ही इसका उपयोग कर सकते हैं।* "
    )
    await message.reply_text(help_text)

# --- सुरक्षा और लॉजिक ---

@app.on_message(filters.text & filters.private & ~filters.command(["start", "help", "add", "rmv", "list", "change"]))
async def handle_pass(client, message):
    uid = message.from_user.id
    if uid in waiting_for_password:
        if message.text == BOT_PASSWORD:
            waiting_for_password.remove(uid)
            if message.from_user.username:
                allowed_users.add(message.from_user.username)
            await message.reply_text("✅ **Access Granted!** अब आप वीडियो भेज सकते हैं। 📹")
        else:
            await message.reply_text("❌ गलत पासवर्ड! फिर से कोशिश करें।")

@app.on_message(filters.video & filters.private)
async def video_handler(client, message):
    user = message.from_user.username
    if user != ADMIN_USERNAME and user not in allowed_users:
        return await message.reply_text("❌ आपके पास एक्सेस नहीं है। एडमिन से संपर्क करें।")
    
    user_video_cache[message.from_user.id] = message
    await message.reply_text("📥 **वीडियो प्राप्त हुआ!**\n\n🖼️ अब कृपया उस वीडियो के लिए थंबनेल (फोटो) भेजें।")

@app.on_message(filters.photo & filters.private)
async def photo_handler(client, message):
    uid = message.from_user.id
    if uid not in user_video_cache:
        return await message.reply_text("⚠️ कृपया पहले वीडियो भेजें!")
    
    msg = await message.reply_text("⚡ **प्रोसेसिंग शुरू हो रही है...**")
    v_path, t_path = None, None
    try:
        prev_time = [time.time()]
        
        # फास्ट पैरेलल डाउनलोड
        v_path = await user_video_cache[uid].download(
            progress=progress_bar, progress_args=(msg, "वीडियो डाउनलोड हो रहा है...", prev_time)
        )
        t_path = await message.download()
        
        await msg.edit_text("📤 **अपलोड किया जा रहा है...**")
        prev_time[0] = time.time()
        
        await client.send_video(
            chat_id=message.chat.id, 
            video=v_path, 
            thumb=t_path, 
            caption="🎉 **कार्य पूर्ण!** यहाँ आपका वीडियो है।\n\n🤖 @ThumbnailBot",
            progress=progress_bar, progress_args=(msg, "वीडियो अपलोड हो रहा है...", prev_time)
        )
        await msg.delete()
        
    except Exception as e:
        await msg.edit_text(f"❌ गड़बड़ हुई: {e}")
    finally:
        # 🧹 ऑटो क्लीनअप (Storage Protection)
        if v_path and os.path.exists(v_path): os.remove(v_path)
        if t_path and os.path.exists(t_path): os.remove(t_path)
        if uid in user_video_cache: del user_video_cache[uid]

# --- बॉट लॉन्च ---
if __name__ == "__main__":
    Thread(target=run_web).start()
    print("🤖 Professional Bot is starting...")
    app.run()
