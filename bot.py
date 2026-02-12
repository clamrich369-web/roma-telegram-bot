from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import *
from datetime import datetime

TOKEN = "YOUR_NEW_TOKEN"
ADMIN_IDS = [289763127]

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ================= DATA =================
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

CARD_NUMBER = "6219-8618-1166-9158"
CARD_OWNER = "امین آقازاده"
INSTAGRAM = "@roma.italianfoods"
PHONE = "09141604866"

users = {}
carts = {}
orders = {}
waiting_receipt = set()
feedback_wait = set()

# ================= START =================
@dp.message_handler(commands=['start'])
async def start(message):
    uid = message.from_user.id
    if uid in users:
        await show_main_menu(message)
    else:
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("📱 ارسال شماره تلفن", request_contact=True))
        await message.answer("🍝 به ROMA خوش آمدید\nلطفاً شماره تلفن خود را ارسال کنید", reply_markup=kb)

# ================= REGISTER =================
@dp.message_handler(content_types=['contact'])
async def register(message):
    uid = message.from_user.id
    users[uid] = {
        "name": message.from_user.full_name,
        "phone": message.contact.phone_number
    }
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
    await message.answer(f"📞 تماس: {PHONE}")

@dp.message_handler(lambda m: m.text == "📷 اینستاگرام")
async def instagram(message):
    await message.answer(f"📷 اینستاگرام:\n{INSTAGRAM}")

# ================= MENU =================
@dp.message_handler(lambda m: m.text == "🍽 منوی غذا")
async def menu(message):
    kb = InlineKeyboardMarkup(row_width=2)
    for food, price in MENU.items():
        kb.add(InlineKeyboardButton(f"{food} - {price}", callback_data=f"food:{food}"))
    kb.add(InlineKeyboardButton("🛒 سبد خرید", callback_data="cart"))
    await message.answer("غذای مورد نظر را انتخاب کنید:", reply_markup=kb)

# ================= ADD FOOD =================
@dp.callback_query_handler(lambda c: c.data.startswith("food:"))
async def choose_qty(call):
    food = call.data.split(":")[1]
    kb = InlineKeyboardMarkup()
    for i in range(1, 6):
        kb.add(InlineKeyboardButton(str(i), callback_data=f"add:{food}:{i}"))
    kb.add(InlineKeyboardButton("⬅ بازگشت", callback_data="back_menu"))
    await call.message.edit_text(f"تعداد {food} را انتخاب کنید:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("add:"))
async def add_cart(call):
    _, food, qty = call.data.split(":")
    uid = call.from_user.id
    carts.setdefault(uid, {})
    carts[uid][food] = carts[uid].get(food, 0) + int(qty)

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("🍽 افزودن غذای دیگر", callback_data="back_menu"),
        InlineKeyboardButton("🛒 سبد خرید", callback_data="cart")
    )
    await call.message.edit_text("✅ به سبد اضافه شد", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "back_menu")
async def back_menu(call):
    await menu(call.message)

# ================= CART =================
@dp.callback_query_handler(lambda c: c.data == "cart")
async def cart(call):
    uid = call.from_user.id
    if not carts.get(uid):
        await call.message.edit_text("❌ سبد خرید خالی است")
        return

    total = 0
    text = "🛒 سبد خرید\n\n"
    kb = InlineKeyboardMarkup()

    for food, qty in carts[uid].items():
        price = MENU[food] * qty
        total += price
        text += f"{food} × {qty} = {price}\n"
        kb.add(InlineKeyboardButton(f"❌ حذف {food}", callback_data=f"del:{food}"))

    text += f"\n💰 جمع کل: {total}"
    kb.add(InlineKeyboardButton("✅ تایید سفارش", callback_data="confirm"))
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("del:"))
async def delete_item(call):
    carts[call.from_user.id].pop(call.data.split(":")[1], None)
    await cart(call)

# ================= PAYMENT =================
@dp.callback_query_handler(lambda c: c.data == "confirm")
async def confirm(call):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("💳 کارت به کارت", callback_data="pay_card"),
        InlineKeyboardButton("🏠 پرداخت حضوری", callback_data="pay_cash")
    )
    await call.message.edit_text("روش پرداخت را انتخاب کنید:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "pay_card")
async def pay_card(call):
    uid = call.from_user.id
    total = sum(MENU[f]*q for f,q in carts[uid].items())
    waiting_receipt.add(uid)

    await call.message.edit_text(
        f"💳 کارت به کارت\n\n"
        f"💰 مبلغ: {total}\n"
        f"🏦 شماره کارت:\n{CARD_NUMBER}\n"
        f"👤 به نام: {CARD_OWNER}\n\n"
        "📸 لطفاً رسید پرداخت را ارسال کنید"
    )

@dp.message_handler(content_types=['photo'])
async def receipt(message):
    uid = message.from_user.id
    if uid not in waiting_receipt:
        return

    waiting_receipt.remove(uid)
    orders[uid] = carts[uid]

    for admin in ADMIN_IDS:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🍝 غذا آماده شد", callback_data=f"ready:{uid}"))
        await bot.send_photo(
            admin,
            message.photo[-1].file_id,
            caption=f"💳 رسید پرداخت\n👤 {users[uid]['name']}",
            reply_markup=kb
        )

    carts.pop(uid, None)
    await message.answer("✅ رسید ارسال شد\n⏳ منتظر تایید")

@dp.callback_query_handler(lambda c: c.data == "pay_cash")
async def pay_cash(call):
    uid = call.from_user.id
    orders[uid] = carts[uid]

    for admin in ADMIN_IDS:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🍝 غذا آماده شد", callback_data=f"ready:{uid}"))
        await bot.send_message(
            admin,
            f"🏠 پرداخت حضوری\n👤 {users[uid]['name']}",
            reply_markup=kb
        )

    carts.pop(uid, None)
    await call.message.edit_text("✅ سفارش حضوری ثبت شد")

# ================= READY =================
@dp.callback_query_handler(lambda c: c.data.startswith("ready"))
async def ready(call):
    uid = int(call.data.split(":")[1])
    await bot.send_message(uid, "🍝 غذای شما آماده شد، نوش جان ❤️")

# ================= FEEDBACK =================
@dp.message_handler(lambda m: m.text == "💬 انتقادات و پیشنهادات")
async def feedback_start(message):
    feedback_wait.add(message.from_user.id)
    await message.answer("✍️ نظر خود را بنویسید")

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
    await message.answer(
        f"📊 گزارش\n👥 کاربران: {len(users)}\n🛒 سفارش‌ها: {len(orders)}"
    )

# ================= RUN =================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
