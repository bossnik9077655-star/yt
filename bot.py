import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from flask import Flask
from threading import Thread

# --- वेब सर्वर (Render को जगाए रखने के लिए) ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is Running Live 24/7!"

def run_web():
    # Render के लिए host हमेशा 0.0.0.0 होना चाहिए
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port) 

# --- टेलीग्राम बॉट सेटअप ---
API_ID = 34793313
API_HASH = "9f2f3b666be702826a6da45024bf4ec7"
BOT_TOKEN = "8698411409:AAH8tP0Lvd1iml2kUJVDGg7R9CEJmNem_Vc"

app = Client("ThumbnailBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

ADMIN_USERNAME = "Nikboss9"
BOT_PASSWORD = "nikhil"

allowed_users = set()  
waiting_for_password = set()  
user_video_cache = {}  

# --- कमांड्स और लॉजिक ---

@app.on_message(filters.command("add") & filters.private)
async def add_user(client, message):
    if message.from_user.username != ADMIN_USERNAME:
        return await message.reply_text("❌ Permission Denied!")
    try:
        new_user = message.text.split(" ")[1].replace("@", "")
        allowed_users.add(new_user)
        await message.reply_text(f"✅ @{new_user} Added!")
    except:
        await message.reply_text("Usage: `/add username`")

@app.on_message(filters.command("rmv") & filters.private)
async def remove_user(client, message):
    if message.from_user.username != ADMIN_USERNAME:
        return await message.reply_text("❌ Permission Denied!")
    try:
        rem_user = message.text.split(" ")[1].replace("@", "")
        allowed_users.discard(rem_user)
        await message.reply_text(f"✅ @{rem_user} Removed!")
    except:
        await message.reply_text("Usage: `/rmv username`")

@app.on_message(filters.command("list") & filters.private)
async def list_users(client, message):
    if message.from_user.username != ADMIN_USERNAME: return
    users = "\n".join([f"👤 @{u}" for u in allowed_users]) or "No users."
    await message.reply_text(f"📋 **Users:**\n\n{users}")

@app.on_message(filters.command("change") & filters.private)
async def change_pass(client, message):
    global BOT_PASSWORD
    if message.from_user.username != ADMIN_USERNAME: return
    try:
        BOT_PASSWORD = message.text.split(" ")[1]
        await message.reply_text(f"🔐 New Pass: `{BOT_PASSWORD}`")
    except: pass

@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user = message.from_user.username or message.from_user.first_name
    text = f"✨ **नमस्ते @{user}!**\nमैं एक प्रोफेशनल थंबनेल बॉट हूँ। 🤖"
    if user == ADMIN_USERNAME or user in allowed_users:
        await message.reply_text(f"{text}\n\n✅ आप वेरिफाइड हैं! वीडियो भेजें।")
    else:
        waiting_for_password.add(message.from_user.id)
        await message.reply_text(f"{text}\n\n🔒 **पासवर्ड डालें:**")

@app.on_message(filters.command("help") & filters.private)
async def help(client, message):
    await message.reply_text("📖 **मदद:**\n1. वीडियो भेजें\n2. फोटो भेजें\n3. जादू देखें! 🎉")

@app.on_message(filters.text & filters.private & ~filters.command(["start", "help", "add", "rmv", "list", "change"]))
async def pass_check(client, message):
    uid = message.from_user.id
    if uid in waiting_for_password:
        if message.text == BOT_PASSWORD:
            waiting_for_password.remove(uid)
            allowed_users.add(message.from_user.username)
            await message.reply_text("✅ Access Granted! वीडियो भेजें।")
        else:
            await message.reply_text("❌ Wrong Password!")

@app.on_message(filters.video & filters.private)
async def vid_rec(client, message):
    if message.from_user.username != ADMIN_USERNAME and message.from_user.username not in allowed_users:
        return await message.reply_text("❌ No Access!")
    user_video_cache[message.from_user.id] = message
    await message.reply_text("📥 वीडियो मिला! अब **फोटो (Thumbnail)** भेजें।")

@app.on_message(filters.photo & filters.private)
async def thumb_rec(client, message):
    uid = message.from_user.id
    if uid not in user_video_cache:
        return await message.reply_text("⚠️ पहले वीडियो भेजें!")
    
    msg = await message.reply_text("⚡ **प्रोसेसिंग...**")
    v_path, t_path = None, None
    try:
        # पैरेलल डाउनलोड
        v_path, t_path = await asyncio.gather(user_video_cache[uid].download(), message.download())
        await msg.edit_text("📤 अपलोड हो रहा है...")
        await client.send_video(chat_id=message.chat.id, video=v_path, thumb=t_path, caption="✅ Done!")
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")
    finally:
        # 🧹 ऑटो डिलीट (Storage Cleanup)
        if v_path and os.path.exists(v_path): os.remove(v_path)
        if t_path and os.path.exists(t_path): os.remove(t_path)
        if uid in user_video_cache: del user_video_cache[uid]

# --- रन करने का तरीका ---
if __name__ == "__main__":
    # वेब सर्वर को अलग धागे (thread) में चलाना
    Thread(target=run_web).start()
    print("🤖 Bot is starting...")
    app.run()

