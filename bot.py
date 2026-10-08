import sqlite3
import os
import asyncio
from datetime import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ========== تنظیمات ==========
BOT_TOKEN = "8893168720:AAEKfFC9W_fy1s9Im_-oljGHye0vW1xKUtQ"
ADMIN_ID = 6549666251
ADMIN_USERNAME = "@Shamal1374"

DB = "bot.db"

# ========== حالت‌ها ==========
(ASK_NAME, ASK_LASTNAME, ASK_HABITS, ASK_PHONE, ASK_ADDRESS, ASK_PHOTO) = range(6)
(ADD_NAME, ADD_LASTNAME, ADD_HABITS, ADD_PHONE, ADD_ADDRESS,
 ADD_STATUS, ADD_DUTY, ADD_TG, ADD_WA) = range(10, 19)
(EDIT_VALUE,) = range(20, 21)
(SEARCH_INPUT,) = range(30, 31)


# ========== دیتابیس ==========
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS friends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, lastname TEXT, habits TEXT,
        phone TEXT, address TEXT, status TEXT, duty TEXT,
        tg_id TEXT, wa_id TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        name TEXT, lastname TEXT, habits TEXT,
        phone TEXT, address TEXT, photo TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, friend_id INTEGER, seen_at TEXT
    )""")
    conn.commit()
    conn.close()

init_db()


# ========== کیبورد Reply (زیر باکس تایپ) ==========
def admin_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("➕ افزودن دوست")],
        [KeyboardButton("📋 لیست دوستان"), KeyboardButton("📊 آمار کلی")],
        [KeyboardButton("👥 آمار هر دوست")],
        [KeyboardButton("👤 کاربران ثبت‌شده"), KeyboardButton("🔔 آخرین بازدیدها")],
    ], resize_keyboard=True)


def user_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("👥 دوستان"), KeyboardButton("📝 ثبت خودم")],
        [KeyboardButton("🔍 جستجو")],
    ], resize_keyboard=True)


# ========== /start ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid == ADMIN_ID:
        await update.message.reply_text(
            f"سلام مدیر عزیز 👋\nخوش آمدی {ADMIN_USERNAME}\n\nاز منوی زیر استفاده کن:",
            reply_markup=admin_menu()
        )
    else:
        await update.message.reply_text(
            "سلام 👋\nبه ربات خوش آمدی.\nاز منوی زیر استفاده کن:",
            reply_markup=user_menu()
        )


# ========== منوی اصلی (دکمه‌ها) ==========
async def menu_dispatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = update.effective_user.id

    if uid == ADMIN_ID:
        if text == "➕ افزودن دوست":
            await update.message.reply_text("اسم دوست را وارد کن:")
            context.user_data.clear()
            return ADD_NAME
        elif text == "📋 لیست دوستان":
            await admin_friends_msg(update)
        elif text == "📊 آمار کلی":
            await admin_stats_msg(update)
        elif text == "👥 آمار هر دوست":
            await admin_friend_stats_msg(update)
        elif text == "👤 کاربران ثبت‌شده":
            await admin_users_msg(update)
        elif text == "🔔 آخرین بازدیدها":
            await admin_recent_msg(update)
    else:
        if text == "👥 دوستان":
            await user_list_msg(update)
        elif text == "📝 ثبت خودم":
            return await register_me_msg(update, context)
        elif text == "🔍 جستجو":
            await update.message.reply_text("اسم یا تخلص را بنویس تا جستجو کنم:")
            return SEARCH_INPUT
    return ConversationHandler.END


# ========== آمار کلی (پیام) ==========
async def admin_stats_msg(update):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM friends"); f = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users"); u = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM notifications"); n = c.fetchone()[0]
    conn.close()
    await update.message.reply_text(
        f"📊 *آمار کلی ربات*\n\n"
        f"👥 تعداد دوستان: {f}\n"
        f"👤 کاربران ثبت‌شده: {u}\n"
        f"👁 کل بازدیدها: {n}",
        parse_mode="Markdown"
    )


# ========== لیست دوستان (مدیر) ==========
async def admin_friends_msg(update):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT id, name, lastname FROM friends")
    friends = c.fetchall()
    conn.close()
    if not friends:
        await update.message.reply_text("هنوز دوستی اضافه نشده.")
        return
    kb = []
    for fid, name, lastname in friends:
        kb.append([InlineKeyboardButton(f"👤 {name} {lastname}", callback_data=f"fd_{fid}")])
    await update.message.reply_text("لیست دوستان:", reply_markup=InlineKeyboardMarkup(kb))


async def friend_manage(update, context):
    q = update.callback_query
    await q.answer()
    if q.from_user.id != ADMIN_ID:
        return
    fid = int(q.data.split("_")[1])
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("""SELECT name,lastname,habits,phone,address,status,duty,tg_id,wa_id
                 FROM friends WHERE id=?""", (fid,))
    f = c.fetchone()
    conn.close()
    text = (
        f"👤 *{f[0]} {f[1]}*\n\n"
        f"🎯 عادت‌ها: {f[2]}\n"
        f"📞 شماره: {f[3]}\n"
        f"🏠 آدرس: {f[4]}\n"
        f"❤️ وضعیت: {f[5]}\n"
        f"💼 وظیفه: {f[6]}\n"
        f"📱 تلگرام: {f[7]}\n"
        f"💬 واتساپ: {f[8] or '—'}"
    )
    kb = [
        [InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_{fid}")],
        [InlineKeyboardButton("🗑 حذف", callback_data=f"del_{fid}")],
    ]
    await q.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")


# ========== حذف با تأیید/لغو (در پیام) ==========
async def delete_confirm(update, context):
    q = update.callback_query
    await q.answer()
    if q.from_user.id != ADMIN_ID:
        return
    fid = int(q.data.split("_")[1])
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT name, lastname FROM friends WHERE id=?", (fid,))
    f = c.fetchone()
    conn.close()
    kb = [
        [InlineKeyboardButton("🟢 تأیید حذف", callback_data=f"delyes_{fid}")],
        [InlineKeyboardButton("🔵 لغو", callback_data=f"delno_{fid}")],
    ]
    await q.message.reply_text(
        f"⚠️ آیا مطمئنی می‌خواهی *{f[0]} {f[1]}* را حذف کنی؟",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )


async def delete_yes(update, context):
    q = update.callback_query
    await q.answer()
    if q.from_user.id != ADMIN_ID:
        return
    fid = int(q.data.split("_")[1])
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("DELETE FROM friends WHERE id=?", (fid,))
    c.execute("DELETE FROM notifications WHERE friend_id=?", (fid,))
    conn.commit(); conn.close()
    await q.message.edit_text("🟢 دوست با موفقیت حذف شد.")


async def delete_no(update, context):
    q = update.callback_query
    await q.answer()
    await q.message.edit_text("🔵 حذف لغو شد.")


# ========== ویرایش ==========
async def edit_menu(update, context):
    q = update.callback_query
    await q.answer()
    if q.from_user.id != ADMIN_ID:
        return
    fid = int(q.data.split("_")[1])
    context.user_data["edit_fid"] = fid
    kb = [
        [InlineKeyboardButton("اسم", callback_data="ef_name"),
         InlineKeyboardButton("تخلص", callback_data="ef_lastname")],
        [InlineKeyboardButton("عادت‌ها", callback_data="ef_habits"),
         InlineKeyboardButton("شماره", callback_data="ef_phone")],
        [InlineKeyboardButton("آدرس", callback_data="ef_address"),
         InlineKeyboardButton("وضعیت", callback_data="ef_status")],
        [InlineKeyboardButton("وظیفه", callback_data="ef_duty")],
        [InlineKeyboardButton("تلگرام", callback_data="ef_tg_id"),
         InlineKeyboardButton("واتساپ", callback_data="ef_wa_id")],
    ]
    await q.message.reply_text("کدام فیلد را ویرایش کنم؟", reply_markup=InlineKeyboardMarkup(kb))


async def edit_field(update, context):
    q = update.callback_query
    await q.answer()
    if q.from_user.id != ADMIN_ID:
        return
    field = q.data.replace("ef_", "")
    context.user_data["edit_field"] = field
    await q.message.reply_text(f"مقدار جدید برای *{field}* را بفرست:", parse_mode="Markdown")
    return EDIT_VALUE


async def edit_save(update, context):
    fid = context.user_data["edit_fid"]
    field = context.user_data["edit_field"]
    val = update.message.text
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute(f"UPDATE friends SET {field}=? WHERE id=?", (val, fid))
    conn.commit(); conn.close()
    await update.message.reply_text("🟢 ویرایش ذخیره شد.", reply_markup=admin_menu())
    return ConversationHandler.END


# ========== آمار هر دوست ==========
async def admin_friend_stats_msg(update):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT id, name, lastname FROM friends")
    friends = c.fetchall()
    conn.close()
    if not friends:
        await update.message.reply_text("هنوز دوستی اضافه نشده.")
        return
    kb = []
    for fid, name, lastname in friends:
        kb.append([InlineKeyboardButton(f"{name} {lastname}", callback_data=f"statf_{fid}")])
    await update.message.reply_text(
        "برای دیدن آمار هر دوست، روی اسمش کلیک کن:",
        reply_markup=InlineKeyboardMarkup(kb)
    )


async def friend_stat_detail(update, context):
    q = update.callback_query
    await q.answer()
    if q.from_user.id != ADMIN_ID:
        return
    fid = int(q.data.split("_")[1])
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT name, lastname FROM friends WHERE id=?", (fid,))
    f = c.fetchone()
    c.execute("SELECT COUNT(*) FROM notifications WHERE friend_id=?", (fid,))
    cnt = c.fetchone()[0]
    conn.close()
    kb = [
        [InlineKeyboardButton(f"👁 {cnt} بازدید — مشاهده بینندگان", callback_data=f"viewers_{fid}")],
    ]
    await q.message.reply_text(
        f"📊 *آمار بازدید {f[0]} {f[1]}*\n\n"
        f"👁 تعداد کل بازدید: {cnt}",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )


async def friend_viewers(update, context):
    q = update.callback_query
    await q.answer()
    if q.from_user.id != ADMIN_ID:
        return
    fid = int(q.data.split("_")[1])
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT name, lastname FROM friends WHERE id=?", (fid,))
    f = c.fetchone()
    c.execute("""SELECT user_id, seen_at FROM notifications
                 WHERE friend_id=? ORDER BY id DESC""", (fid,))
    rows = c.fetchall()
    conn.close()
    if not rows:
        await q.message.reply_text("هنوز کسی این دوست را ندیده.")
        return
    text = f"👥 *بینندگان {f[0]} {f[1]}*\n\n"
    for i, (uid, seen) in enumerate(rows, 1):
        text += f"{i}. `{uid}` — {seen}\n"
    await q.message.reply_text(text, parse_mode="Markdown")


# ========== کاربران ثبت‌شده ==========
async def admin_users_msg(update):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT user_id, name, lastname, phone, photo FROM users")
    users = c.fetchall()
    conn.close()
    if not users:
        await update.message.reply_text("هنوز کاربری ثبت نشده.")
        return
    for uid, name, lastname, phone, photo in users:
        text = f"👤 *{name} {lastname}*\n📞 {phone}\n🆔 `{uid}`"
        if photo and os.path.exists(photo):
            with open(photo, "rb") as f:
                await update.message.reply_photo(f, caption=text, parse_mode="Markdown")
        else:
            await update.message.reply_text(text, parse_mode="Markdown")


# ========== آخرین بازدیدها ==========
async def admin_recent_msg(update):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("""SELECT n.user_id, f.name, f.lastname, n.seen_at
                 FROM notifications n
                 JOIN friends f ON f.id = n.friend_id
                 ORDER BY n.id DESC LIMIT 20""")
    rows = c.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("هنوز بازدیدی ثبت نشده.")
        return
    text = "🔔 *آخرین ۲۰ بازدید:*\n\n"
    for uid, fname, flast, seen in rows:
        text += f"👤 `{uid}` → {fname} {flast} — {seen}\n"
    await update.message.reply_text(text, parse_mode="Markdown")


# ========== افزودن دوست ==========
async def add_start(update, context):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("اسم دوست را وارد کن:")
    return ADD_NAME

async def add_name(update, context):
    context.user_data["f_name"] = update.message.text
    await update.message.reply_text("تخلص؟")
    return ADD_LASTNAME

async def add_lastname(update, context):
    context.user_data["f_lastname"] = update.message.text
    await update.message.reply_text("عادت‌ها؟")
    return ADD_HABITS

async def add_habits(update, context):
    context.user_data["f_habits"] = update.message.text
    await update.message.reply_text("شماره تلیفون؟")
    return ADD_PHONE

async def add_phone(update, context):
    context.user_data["f_phone"] = update.message.text
    await update.message.reply_text("آدرس؟")
    return ADD_ADDRESS

async def add_address(update, context):
    context.user_data["f_address"] = update.message.text
    await update.message.reply_text("وضعیت (زنده/مرده)؟")
    return ADD_STATUS

async def add_status(update, context):
    context.user_data["f_status"] = update.message.text
    await update.message.reply_text("وظیفه؟")
    return ADD_DUTY

async def add_duty(update, context):
    context.user_data["f_duty"] = update.message.text
    await update.message.reply_text("آیدی تلگرام؟ (مثلاً @username)")
    return ADD_TG

async def add_tg(update, context):
    context.user_data["f_tg"] = update.message.text
    await update.message.reply_text("شماره واتساپ؟ (اگر نداری بنویس: -)")
    return ADD_WA

async def add_wa(update, context):
    ud = context.user_data
    wa = update.message.text if update.message.text != "-" else None
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("""INSERT INTO friends
        (name,lastname,habits,phone,address,status,duty,tg_id,wa_id)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (ud["f_name"], ud["f_lastname"], ud["f_habits"], ud["f_phone"],
         ud["f_address"], ud["f_status"], ud["f_duty"], ud["f_tg"], wa))
    conn.commit(); conn.close()
    await update.message.reply_text("🟢 دوست با موفقیت اضافه شد.", reply_markup=admin_menu())
    return ConversationHandler.END


# ========== لیست دوستان (کاربر عادی) ==========
async def user_list_msg(update):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT id, name, lastname FROM friends")
    friends = c.fetchall()
    conn.close()
    if not friends:
        await update.message.reply_text("هنوز دوستی اضافه نشده است.")
        return
    kb = []
    for fid, name, lastname in friends:
        kb.append([InlineKeyboardButton(f"👤 {name} {lastname}", callback_data=f"friend_{fid}")])
    await update.message.reply_text("یک دوست را انتخاب کن:", reply_markup=InlineKeyboardMarkup(kb))


# ========== کلیک روی دوست ==========
async def friend_click(update, context):
    q = update.callback_query
    await q.answer()
    fid = int(q.data.split("_")[1])
    uid = q.from_user.id

    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    exists = c.fetchone()
    conn.close()

    if exists:
        await show_friend_details(q, fid, uid)
    else:
        context.user_data["pending_friend"] = fid
        await q.message.reply_text("اول باید خودت را معرفی کنی.\n\nاسمت چیست؟")
        return ASK_NAME


# ========== ثبت کاربر جدید ==========
async def register_me_msg(update, context):
    uid = update.effective_user.id
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    exists = c.fetchone()
    conn.close()
    if exists:
        await update.message.reply_text("تو قبلاً ثبت‌نام کرده‌ای ✅", reply_markup=user_menu())
        return ConversationHandler.END
    context.user_data["pending_friend"] = None
    await update.message.reply_text("اسمت چیست؟")
    return ASK_NAME


async def ask_name(update, context):
    context.user_data["u_name"] = update.message.text
    await update.message.reply_text("تخلصت؟")
    return ASK_LASTNAME

async def ask_lastname(update, context):
    context.user_data["u_lastname"] = update.message.text
    await update.message.reply_text("عادت‌هایت؟")
    return ASK_HABITS

async def ask_habits(update, context):
    context.user_data["u_habits"] = update.message.text
    await update.message.reply_text("شماره تلیفونت؟")
    return ASK_PHONE

async def ask_phone(update, context):
    context.user_data["u_phone"] = update.message.text
    await update.message.reply_text("آدرست؟")
    return ASK_ADDRESS

async def ask_address(update, context):
    context.user_data["u_address"] = update.message.text
    await update.message.reply_text("یک عکس از خودت بفرست 📷")
    return ASK_PHOTO

async def ask_photo(update, context):
    uid = update.effective_user.id
    photo = update.message.photo[-1] if update.message.photo else None
    path = None
    if photo:
        os.makedirs("photos", exist_ok=True)
        f = await photo.get_file()
        path = f"photos/{uid}.jpg"
        await f.download_to_drive(path)
    ud = context.user_data
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users VALUES (?,?,?,?,?,?,?)",
              (uid, ud["u_name"], ud["u_lastname"], ud["u_habits"],
               ud["u_phone"], ud["u_address"], path))
    conn.commit(); conn.close()

    await update.message.reply_text(
        f"🟢 خوش آمدی {ud['u_name']}!\nثبت‌نامت با موفقیت انجام شد ✅\n"
        f"حالا می‌توانی دوستان را ببینی.",
        reply_markup=user_menu()
    )
    try:
        await context.bot.send_message(
            ADMIN_ID,
            f"👤 *کاربر جدید ثبت شد*\n\n"
            f"اسم: {ud['u_name']} {ud['u_lastname']}\n"
            f"🆔 `{uid}`",
            parse_mode="Markdown"
        )
    except:
        pass

    fid = ud.get("pending_friend")
    if fid:
        await show_friend_details(update, fid, uid, is_message=True)
    return ConversationHandler.END


# ========== نمایش جزییات دوست ==========
async def show_friend_details(source, fid, uid, is_message=False):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("""SELECT name,lastname,habits,phone,address,status,duty,tg_id,wa_id
                 FROM friends WHERE id=?""", (fid,))
    f = c.fetchone()
    c.execute("SELECT name,lastname FROM users WHERE user_id=?", (uid,))
    u = c.fetchone()

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute("INSERT INTO notifications (user_id, friend_id, seen_at) VALUES (?,?,?)",
              (uid, fid, now))
    conn.commit(); conn.close()

    text = (
        f"👤 *{f[0]} {f[1]}*\n\n"
        f"🎯 عادت‌ها: {f[2]}\n"
        f"📞 شماره: {f[3]}\n"
        f"🏠 آدرس: {f[4]}\n"
        f"❤️ وضعیت: {f[5]}\n"
        f"💼 وظیفه: {f[6]}\n"
        f"📱 تلگرام: {f[7]}\n"
        f"💬 واتساپ: {f[8] or '—'}"
    )
    await source.message.reply_text(text, parse_mode="Markdown")

    if u:
        admin_msg = (
            f"🔔 *اعلان بازدید جدید*\n\n"
            f"👤 کاربر: {u[0]} {u[1]}\n"
            f"🆔 `{uid}`\n"
            f"👁 جزییات *{f[0]} {f[1]}* را دید.\n"
            f"🕐 {now}"
        )
    else:
        admin_msg = (
            f"🔔 *اعلان بازدید جدید*\n\n"
            f"🆔 `{uid}`\n"
            f"👁 جزییات *{f[0]} {f[1]}* را دید.\n"
            f"🕐 {now}"
        )
    try:
        await source.get_bot().send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
    except:
        pass


# ========== جستجو ==========
async def search_do(update, context):
    term = update.message.text.strip()
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("""SELECT id, name, lastname FROM friends
                 WHERE name LIKE ? OR lastname LIKE ?""",
              (f"%{term}%", f"%{term}%"))
    rows = c.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("چیزی پیدا نشد.", reply_markup=user_menu())
        return ConversationHandler.END
    kb = []
    for fid, name, lastname in rows:
        kb.append([InlineKeyboardButton(f"👤 {name} {lastname}", callback_data=f"friend_{fid}")])
    await update.message.reply_text("نتایج جستجو:", reply_markup=InlineKeyboardMarkup(kb))
    return ConversationHandler.END


# ========== لغو ==========
async def cancel(update, context):
    uid = update.effective_user.id
    menu = admin_menu() if uid == ADMIN_ID else user_menu()
    await update.message.reply_text("🔵 لغو شد.", reply_markup=menu)
    return ConversationHandler.END


# ========== main ==========
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # منوی دکمه‌ای (Reply)
    menu_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, menu_dispatch)],
        states={
            ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
            ADD_LASTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_lastname)],
            ADD_HABITS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_habits)],
            ADD_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_phone)],
            ADD_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_address)],
            ADD_STATUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_status)],
            ADD_DUTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_duty)],
            ADD_TG: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_tg)],
            ADD_WA: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_wa)],
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_LASTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_lastname)],
            ASK_HABITS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_habits)],
            ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            ASK_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_address)],
            ASK_PHOTO: [MessageHandler(filters.PHOTO | (filters.TEXT & ~filters.COMMAND), ask_photo)],
            SEARCH_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_do)],
            EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_save)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    # کلیک روی دوست (کاربر عادی، وقتی ثبت‌نام نکرده)
    register_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(friend_click, pattern="^friend_")],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_LASTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_lastname)],
            ASK_HABITS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_habits)],
            ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            ASK_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_address)],
            ASK_PHOTO: [MessageHandler(filters.PHOTO | (filters.TEXT & ~filters.COMMAND), ask_photo)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    # ویرایش
    edit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_field, pattern="^ef_")],
        states={
            EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_save)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(edit_conv)
    app.add_handler(register_conv)
    app.add_handler(menu_conv)

    # callbackها
    app.add_handler(CallbackQueryHandler(friend_manage, pattern="^fd_"))
    app.add_handler(CallbackQueryHandler(delete_confirm, pattern="^del_"))
    app.add_handler(CallbackQueryHandler(delete_yes, pattern="^delyes_"))
    app.add_handler(CallbackQueryHandler(delete_no, pattern="^delno_"))
    app.add_handler(CallbackQueryHandler(edit_menu, pattern="^edit_"))
    app.add_handler(CallbackQueryHandler(friend_stat_detail, pattern="^statf_"))
    app.add_handler(CallbackQueryHandler(friend_viewers, pattern="^viewers_"))

    print("ربات روشن شد...")
    app.run_polling()


if __name__ == "__main__":
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    main()
