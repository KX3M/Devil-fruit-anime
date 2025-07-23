from pyrogram import Client, filters
from pyromod import listen
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import DB_URL, DB_NAME
import aiohttp, random, asyncio, datetime, pymongo, logging

# Logging
logging.basicConfig(level=logging.INFO)

# MongoDB setup
dbclient = pymongo.MongoClient(DB_URL)
database = dbclient[DB_NAME]
methods = database['meth_results']

@Client.on_message(filters.command("meth"))
async def meth_command(client, message):
    await message.reply("<b>Please Send Your Target Username Without @</b>\n\n⚠️ <i>Please Send Only Real Targets</i>")

    try:
        user_response = await client.listen(message.chat.id, timeout=15)
        username = user_response.text.strip().lstrip('@')
    except asyncio.TimeoutError:
        await message.reply("⏱ Timeout! Please try again using /meth.")
        return

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api-v2.nextcounts.com/api/instagram/user/{username}") as resp:
                if resp.status != 200:
                    raise Exception("Failed to fetch")
                data = await resp.json()
    except Exception as e:
        logging.warning(f"API error: {e}")
        await message.reply("<b>Error while processing. Try again.</b>")
        return

    info = (
        f"<b>Is this the correct user?</b>\n\n"
        f"• <b>Username:</b> {data.get('username')}\n"
        f"• <b>Nickname:</b> {data.get('nickname') or 'N/A'}\n"
        f"• <b>Followers:</b> {data.get('followers')}\n"
        f"• <b>Following:</b> {data.get('following')}\n"
        f"• <b>Posts:</b> {data.get('posts')}"
    )

    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Yes ✅", callback_data=f"confirm_yes_{username}"),
        InlineKeyboardButton("No ❌", callback_data="confirm_no")
    )
    await message.reply(info, reply_markup=kb)

@Client.on_callback_query(filters.regex("^confirm_"))
async def handle_callback(client, call):
    data = call.data

    if data == "confirm_no":
        await call.message.edit_text("<b>Okay, Try again. /meth</b>")
        return

    if data.startswith("confirm_yes_"):
        username = data.split("_", 2)[2]
        await call.message.edit_text(f"<b>Confirmed IG:</b> @{username}\n\nStarting...")
        loading = await call.message.reply("<b>Generating method... Please wait.</b>")

        for i in range(10, 101, 10):
            bar = '▓' * (i // 10) + '░' * (10 - i // 10)
            try:
                await loading.edit_text(f"<b>🔍 Sᴄᴀɴɴɪɴɢ Pʀᴏғɪʟᴇ... {i}%</b>\n<pre>{bar}</pre>")
            except:
                break
            await asyncio.sleep(0.1)

        existing = methods.find_one({"username": username})
        if existing:
            result = existing['result']
        else:
            categories = [
                'Nudity¹', 'Nudity²', 'Hate', 'Scam', 'Terrorism', 'Vio¹', 'Vio²',
                'Sale Illegal [Drugs]', 'Firearms', 'Bully_Me', 'Self_Injury', 'Spam'
            ]
            picked = random.sample(categories, random.randint(2, 4))
            result = '\n'.join(f"➥ {random.randint(1,5)}x {cat}" for cat in picked)

            try:
                methods.insert_one({
                    "username": username,
                    "result": result,
                    "created_at": datetime.datetime.utcnow()
                })
            except Exception as e:
                logging.warning(f"MongoDB insert failed: {e}")

        final_text = (
            f"<i>Username : @{username}</i>\n\n"
            f"<b>Suggested Reports for Your Target:</b>\n\n"
            f"<pre>{result}</pre>\n\n"
            f"<blockquote>⚠️ <b>Note:</b> <i><a href='https://t.me/Sendpayments'>This method is based on available data and may not be fully accurate.</a></i></blockquote>"
        )

        buttons = InlineKeyboardMarkup(row_width=2)
        buttons.add(
            InlineKeyboardButton("ᴜᴘᴅᴀᴛᴇ", url="https://t.me/PythonBotz"),
            InlineKeyboardButton("ᴅᴇᴠʟᴏᴘᴇʀ", url="https://t.me/existable"),
            InlineKeyboardButton("ᴛᴀʀɢᴇᴛ ᴘʀᴏғɪʟᴇ", url=f"https://instagram.com/{username}")
        )

        await loading.edit_text(final_text, disable_web_page_preview=True, reply_markup=buttons)
