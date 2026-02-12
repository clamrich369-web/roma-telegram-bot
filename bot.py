from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import *
from datetime import date

TOKEN = "8543932711:AAFBzavfn2MunYAvnCKWiAEisUIyEmT04XQ"
ADMIN_IDS = [289763127]

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ===================== DATA =====================
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
    "پیتزا پپرونی": 580,
    "نوشابه": 50
}

CARD_NUMBER = "6219-8618-1166-9158"
CARD_OWNER = "امین آقازاده"

users = {}
carts = {}
orders = {}
stats = {}
feedbacks = []

# ===================== START =====================
@dp.message_handler(commands=["start"])
async def start(message):
    uid = message.from_user.id
    if uid in users:
        await show_main_menu(message)
    else:
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("📱 ارسال شماره تلفن", request_contact=True))
        await message.answer("🍝 به ROMA خوش آمدید\nشماره تلفن خود را ارسال کنید", reply_markup=kb)

# ===================== REGISTER =====================
@dp.message_handler(content_types=ContentType.CONTACT)
async def register(message):
    uid = message.from_user.id
    if uid in users:
        await message.answer("✅ قبلاً ثبت‌نام کرده‌اید")
        return

    users[uid] = {
        "name": message.from_user.full_name,
        "phone": message.contact.phone_number
    }
    carts[uid] = {}
    stats[uid] = {"orders": 0, "total": 0, "ratings": []}

    await message.answer("✅ ثبت‌نام انجام شد")
    await show_main_menu(message)

# ===================== MAIN MENU =====================
async def show_main_menu(message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🍽 منوی غذا", "✍️ انتقاد و پیشنهاد")
    if message.from_user.id in ADMIN_IDS:
        kb.add("📊 گزارش ادمین")
    kb.add("📞 تماس با ما", "📷 اینستاگرام")
    await message.answer("انتخاب کنید:", reply_markup=kb)

# ===================== FOOD MENU =====================
@dp.message_handler(lambda m: m.text == "🍽 منوی غذا")
async def show_menu(message):
    kb = InlineKeyboardMarkup(row_width=2)
    for food, price in MENU.items():
        kb.add(InlineKeyboardButton(f"{food} - {price}", callback_data=f"food:{food}"))
    kb.add(InlineKeyboardButton("🛒 سبد خرید", callback_data="cart"))
    await message.answer("غذای مورد نظر را انتخاب کنید:", reply_markup=kb)

# ===================== ADD FOOD =====================
@dp.callback_query_handler(lambda c: c.data.startswith("food:"))
async def choose_qty(call):
    food = call.data.split(":")[1]
    kb = InlineKeyboardMarkup()
    for i in range(1, 6):
        kb.add(InlineKeyboardButton(str(i), callback_data=f"add:{food}:{i}"))
    kb.add(InlineKeyboardButton("⬅ بازگشت به منو", callback_data="back_menu"))
    await call.message.edit_text(f"تعداد {food} را انتخاب کنید:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("add:"))
async def add_cart(call):
    _, food, qty = call.data.split(":")
    uid = call.from_user.id
    carts[uid][food] = carts[uid].get(food, 0) + int(qty)

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("➕ افزودن غذای دیگر", callback_data="back_menu"),
        InlineKeyboardButton("🛒 سبد خرید", callback_data="cart")
    )
    await call.message.edit_text("✅ به سبد خرید اضافه شد", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "back_menu")
async def back_menu(call):
    await show_menu(call.message)

# ===================== CART =====================
@dp.callback_query_handler(lambda c: c.data == "cart")
async def cart(call):
    uid = call.from_user.id
    if not carts[uid]:
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
    kb.add(
        InlineKeyboardButton("✅ تایید سفارش", callback_data="confirm"),
        InlineKeyboardButton("🍽 افزودن غذا", callback_data="back_menu")
    )
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("del:"))
async def delete_item(call):
    food = call.data.split(":")[1]
    carts[call.from_user.id].pop(food, None)
    await cart(call)

# ===================== CONFIRM =====================
@dp.callback_query_handler(lambda c: c.data == "confirm")
async def confirm(call):
    uid = call.from_user.id
    total = sum(MENU[f] * q for f, q in carts[uid].items())

    orders[uid] = {"items": carts[uid], "total": total}

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("💳 کارت به کارت", callback_data="card"),
        InlineKeyboardButton("🏠 پرداخت حضوری", callback_data="cash")
    )
    await call.message.edit_text("روش پرداخت را انتخاب کنید:", reply_markup=kb)

# ===================== CARD PAYMENT =====================
@dp.callback_query_handler(lambda c: c.data == "card")
async def card(call):
    await call.message.edit_text(
        f"💳 کارت به کارت\n\n{CARD_NUMBER}\n👤 {CARD_OWNER}\n\n"
        f"پس از پرداخت، فیش را ارسال کنید"
    )

@dp.message_handler(content_types=ContentType.PHOTO)
async def receipt(message):
    uid = message.from_user.id
    if uid not in orders:
        return

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✅ تایید پرداخت", callback_data=f"pay_ok:{uid}"),
        InlineKeyboardButton("❌ رد پرداخت", callback_data=f"pay_no:{uid}")
    )

    for admin in ADMIN_IDS:
        await bot.send_photo(
            admin,
            message.photo[-1].file_id,
            caption=f"🧾 فیش پرداخت\n👤 {users[uid]['name']}\n📞 {users[uid]['phone']}\n💰 {orders[uid]['total']}",
            reply_markup=kb
        )

    await message.answer("⏳ فیش در حال بررسی است")

# ===================== ADMIN PAYMENT FLOW =====================
@dp.callback_query_handler(lambda c: c.data.startswith("pay_ok"))
async def pay_ok(call):
    uid = int(call.data.split(":")[1])
    await bot.send_message(uid, "✅ پرداخت تایید شد\n🍝 غذا تا ۱۵ دقیقه آماده می‌شود")

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🍝 غذا آماده شد", callback_data=f"ready:{uid}"))
    await call.message.answer("پرداخت تایید شد", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("pay_no"))
async def pay_no(call):
    uid = int(call.data.split(":")[1])
    await bot.send_message(uid, "❌ پرداخت تایید نشد")

@dp.callback_query_handler(lambda c: c.data.startswith("ready"))
async def ready(call):
    uid = int(call.data.split(":")[1])
    await bot.send_message(uid, "🍝 غذای شما آماده است\n⏳ لطفاً مراجعه کنید")

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("📦 تحویل شد", callback_data=f"done:{uid}"))
    await call.message.answer("آماده تحویل", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("done"))
async def done(call):
    uid = int(call.data.split(":")[1])
    stats[uid]["orders"] += 1
    stats[uid]["total"] += orders[uid]["total"]

    kb = InlineKeyboardMarkup()
    for i in range(1, 6):
        kb.add(InlineKeyboardButton(f"⭐ {i}", callback_data=f"rate:{uid}:{i}"))

    await bot.send_message(uid, "🙏 ممنون از خرید شما\nامتیاز دهید:", reply_markup=kb)

    carts[uid] = {}
    orders.pop(uid)

# ===================== RATING =====================
@dp.callback_query_handler(lambda c: c.data.startswith("rate"))
async def rate(call):
    _, uid, score = call.data.split(":")
    stats[int(uid)]["ratings"].append(int(score))
    await call.message.edit_text("❤️ ممنون از امتیاز شما")

# ===================== FEEDBACK =====================
@dp.message_handler(lambda m: m.text == "✍️ انتقاد و پیشنهاد")
async def feedback_start(message):
    await message.answer("✍️ نظر یا پیشنهاد خود را بنویسید:")

@dp.message_handler(lambda m: m.text and m.text not in [
    "🍽 منوی غذا", "📊 گزارش ادمین", "📞 تماس با ما", "📷 اینستاگرام", "✍️ انتقاد و پیشنهاد"
])
async def feedback_receive(message):
    uid = message.from_user.id
    if uid not in users:
        return

    fb = {
        "name": users[uid]["name"],
        "phone": users[uid]["phone"],
        "text": message.text
    }
    feedbacks.append(fb)

    for admin in ADMIN_IDS:
        await bot.send_message(
            admin,
            f"✍️ انتقاد/پیشنهاد\n👤 {fb['name']}\n📞 {fb['phone']}\n📝 {fb['text']}"
        )

    await message.answer("🙏 ممنون از نظر شما")

# ===================== REPORT =====================
@dp.message_handler(lambda m: m.text == "📊 گزارش ادمین")
async def report(message):
    all_ratings = []
    for s in stats.values():
        all_ratings.extend(s["ratings"])

    avg_rating = round(sum(all_ratings) / len(all_ratings), 2) if all_ratings else 0

    await message.answer(
        f"📊 گزارش ROMA\n\n"
        f"👥 کاربران: {len(users)}\n"
        f"🧾 سفارش‌ها: {sum(s['orders'] for s in stats.values())}\n"
        f"⭐ امتیازها: {len(all_ratings)}\n"
        f"📈 میانگین امتیاز: {avg_rating}\n"
        f"✍️ انتقادات/پیشنهادات: {len(feedbacks)}"
    )

# ===================== RUN =====================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
executor.start_polling(dp)
