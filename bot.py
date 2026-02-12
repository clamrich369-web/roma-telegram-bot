from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import *
import sqlite3
from datetime import datetime

# ================= CONFIG =================
TOKEN = "8543932711:AAFBzavfn2MunYAvnCKWiAEisUIyEmT04XQ"
ADMIN_IDS = [289763127]

CARD_NUMBER = "6219-8618-1166-9158"
CARD_OWNER = "امین آقازاده"
INSTAGRAM = "@roma.italianfoods"
PHONE = "09141604866"

# ================= BOT =================
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ================= DATABASE =================
db = sqlite3.connect("roma.db")
sql = db.cursor()

sql.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    phone TEXT
)
""")

sql.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    items TEXT,
    total INTEGER,
    status TEXT,
    created_at TEXT
)
""")

db.commit()

# ================= MENU =================
MENU = {
    "آلفردو": 450,
    "آناکاردی": 480,
    "پینو": 480,
    "بولونز": 450,
    "ماتریچیانا": 520,
    "گامبرتی (میگو)": 550,
    "لازانیا": 580,
    "پیتزا استیک گوشت": 720,
    "پیتزا مرغ": 580,
    "پیتزا پپرونی": 580
}

carts = {}
feedback_wait = set()

# ================= START =================
@dp.message_handler(commands=['start'])
async def start(message):
    uid = message.from_user.id
    sql.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    if sql.fetchone():
        await show_main_menu(message)
    else:
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("📱 ارسال شماره تلفن", request_contact=True))
        await message.answer("🍝 به ROMA خوش آمدید\nشماره تلفن خود را ارسال کنید", reply_markup=kb)

# ================= REGISTER =================
@dp.message_handler(content_types=['contact'])
async def register(message):
    uid = message.from_user.id
    sql.execute(
        "INSERT OR IGNORE INTO users VALUES (?,?,?)",
        (uid, message.from_user.full_name, message.contact.phone_number)
    )
    db.commit()
    carts.setdefault(uid, {})
    await message.answer("✅ ثبت‌نام انجام شد")
    await show_main_menu(message)

# ================= MAIN MENU =================
async def show_main_menu(message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🍽 منوی غذا")
    kb.add("💬 انتقادات و پیشنهادات")
    if message.from_user.id in ADMIN_IDS:
        kb.add("📊 گزارش ادمین")
    kb.add("📞 تماس با ما", "📷 اینستاگرام")
    await message.answer("انتخاب کنید:", reply_markup=kb)

# ================= CONTACT =================
@dp.message_handler(lambda m: m.text == "📞 تماس با ما")
async def contact(message):
    await message.answer(f"📞 {PHONE}")

@dp.message_handler(lambda m: m.text == "📷 اینستاگرام")
async def instagram(message):
    await message.answer(f"📷 اینستاگرام:\n{INSTAGRAM}")

# ================= FOOD MENU =================
@dp.message_handler(lambda m: m.text == "🍽 منوی غذا")
async def food_menu(message):
    kb = InlineKeyboardMarkup(row_width=2)
    for f, p in MENU.items():
        kb.add(InlineKeyboardButton(f"{f} - {p}", callback_data=f"food:{f}"))
    kb.add(InlineKeyboardButton("🛒 سبد خرید", callback_data="cart"))
    await message.answer("غذا را انتخاب کنید:", reply_markup=kb)

# ================= ADD FOOD =================
@dp.callback_query_handler(lambda c: c.data.startswith("food:"))
async def choose_qty(call):
    food = call.data.split(":")[1]
    kb = InlineKeyboardMarkup()
    for i in range(1, 6):
        kb.add(InlineKeyboardButton(str(i), callback_data=f"add:{food}:{i}"))
    kb.add(InlineKeyboardButton("⬅ بازگشت", callback_data="back"))
    await call.message.edit_text(f"تعداد {food}:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("add:"))
async def add_cart(call):
    _, food, qty = call.data.split(":")
    uid = call.from_user.id
    carts.setdefault(uid, {})
    carts[uid][food] = carts[uid].get(food, 0) + int(qty)
    await call.message.edit_text("✅ اضافه شد")

@dp.callback_query_handler(lambda c: c.data == "back")
async def back(call):
    await food_menu(call.message)

# ================= CART =================
@dp.callback_query_handler(lambda c: c.data == "cart")
async def cart(call):
    uid = call.from_user.id
    if uid not in carts or not carts[uid]:
        await call.message.edit_text("❌ سبد خالی است")
        return

    total = 0
    text = "🛒 سبد خرید\n\n"
    kb = InlineKeyboardMarkup()

    for f, q in carts[uid].items():
        price = MENU[f] * q
        total += price
        text += f"{f} × {q} = {price}\n"
        kb.add(InlineKeyboardButton(f"❌ حذف {f}", callback_data=f"del:{f}"))

    text += f"\n💰 جمع: {total}"
    kb.add(InlineKeyboardButton("✅ ثبت سفارش", callback_data="confirm"))
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("del:"))
async def delete(call):
    carts[call.from_user.id].pop(call.data.split(":")[1], None)
    await cart(call)

# ================= CONFIRM =================
@dp.callback_query_handler(lambda c: c.data == "confirm")
async def confirm(call):
    uid = call.from_user.id
    items = carts[uid]
    total = sum(MENU[f]*q for f,q in items.items())

    sql.execute(
        "INSERT INTO orders (user_id, items, total, status, created_at) VALUES (?,?,?,?,?)",
        (uid, str(items), total, "pending", datetime.now().strftime("%Y-%m-%d %H:%M"))
    )
    db.commit()

    for admin in ADMIN_IDS:
        await bot.send_message(
            admin,
            f"🛒 سفارش جدید\n👤 {uid}\n💰 {total}"
        )

    carts.pop(uid, None)
    await call.message.edit_text("✅ سفارش ثبت شد\n⏳ در حال آماده‌سازی")

# ================= FEEDBACK =================
@dp.message_handler(lambda m: m.text == "💬 انتقادات و پیشنهادات")
async def feedback_start(message):
    feedback_wait.add(message.from_user.id)
    await message.answer("✍️ پیام خود را بنویسید")

@dp.message_handler()
async def feedback_receive(message):
    uid = message.from_user.id
    if uid not in feedback_wait:
        return

    feedback_wait.remove(uid)
    for admin in ADMIN_IDS:
        await bot.send_message(admin, f"💬 نظر جدید:\n{message.text}")

    await message.answer("🙏 ممنون از نظر شما")

# ================= ADMIN REPORT =================
@dp.message_handler(lambda m: m.text == "📊 گزارش ادمین")
async def report(message):
    sql.execute("SELECT COUNT(*) FROM users")
    users_count = sql.fetchone()[0]

    sql.execute("SELECT COUNT(*) FROM orders")
    orders_count = sql.fetchone()[0]

    await message.answer(
        f"📊 گزارش\n👥 کاربران: {users_count}\n🛒 سفارش‌ها: {orders_count}"
    )

# ================= RUN =================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
