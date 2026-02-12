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
# ===================== CONTACT =====================
@dp.message_handler(lambda m: m.text == "📞 تماس با ما")
async def contact_us(message):
    await message.answer(
        "📞 تماس با ما\n\n"
        "شماره تماس:\n"
        "09141604866"
    )

# ===================== INSTAGRAM =====================
@dp.message_handler(lambda m: m.text == "📷 اینستاگرام")
async def instagram(message):
    await message.answer(
        "📷 اینستاگرام ROMA\n\n"
        "@roma.italianfoods\n"
        "https://instagram.com/roma.italianfoods"
    )
    
# ===================== FEEDBACK START =====================
@dp.message_handler(lambda m: m.text == "✍️ انتقاد و پیشنهاد")
async def feedback_start(message):
    await message.answer(
        "✍️ انتقاد یا پیشنهاد خود را بنویسید:\n"
        "پیام شما مستقیماً برای مدیریت ارسال می‌شود."
    )
    
# ===================== FEEDBACK RECEIVE =====================
@dp.message_handler(
    lambda m: m.text
    and m.text not in [
        "🍽 منوی غذا",
        "📊 گزارش ادمین",
        "📞 تماس با ما",
        "📷 اینستاگرام",
        "✍️ انتقاد و پیشنهاد"
    ]
)
async def feedback_receive(message):
    uid = message.from_user.id

    if uid not in users:
        return

    feedback = {
        "name": users[uid]["name"],
        "phone": users[uid]["phone"],
        "text": message.text
    }

    feedbacks.append(feedback)

    # ارسال برای ادمین
    for admin in ADMIN_IDS:
        await bot.send_message(
            admin,
            f"✍️ انتقاد / پیشنهاد جدید\n\n"
            f"👤 نام: {feedback['name']}\n"
            f"📞 تلفن: {feedback['phone']}\n"
            f"📝 متن:\n{feedback['text']}"
        )

    await message.answer("🙏 ممنون از نظر شما")

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

    orders[uid] = {
        "items": carts[uid],
        "total": total
    }

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("💳 کارت به کارت", callback_data="card"),
        InlineKeyboardButton("💵 پرداخت حضوری", callback_data="pay_cash")
    )

    await call.message.edit_text(
        f"💰 مبلغ قابل پرداخت: {total}\nروش پرداخت را انتخاب کنید:",
        reply_markup=kb
    )

# ===================== CASH PAYMENT =====================
@dp.callback_query_handler(lambda c: c.data == "pay_cash")
async def pay_cash(call):
    uid = call.from_user.id
    order = orders.get(uid)

    items_text = "\n".join([f"{k} × {v}" for k, v in order["items"].items()])

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("🍽 غذا آماده است", callback_data=f"food_ready:{uid}"),
        InlineKeyboardButton("❌ بستن سفارش", callback_data=f"close_order:{uid}")
    )

    for admin in ADMIN_IDS:
        await bot.send_message(
            admin,
            f"💵 پرداخت حضوری\n\n👤 {users[uid]['name']}\n📞 {users[uid]['phone']}\n\n🍽 سفارش:\n{items_text}",
            reply_markup=kb
        )

    await call.message.edit_text("✅ سفارش ثبت شد\n⏳ پس از آماده شدن اطلاع داده می‌شود")

# ===================== CARD =====================
@dp.callback_query_handler(lambda c: c.data == "card")
async def card(call):
    uid = call.from_user.id

    total = sum(MENU[f] * q for f, q in carts[uid].items())

    orders[uid] = {
        "items": carts[uid],
        "total": total,
        "payment": "card",
        "status": "waiting_admin"
    }

    await call.message.edit_text(
        f"💳 کارت به کارت\n\n"
        f"{CARD_NUMBER}\n"
        f"👤 {CARD_OWNER}\n\n"
        f"📸 بعد از پرداخت، فیش را ارسال کنید"
    )
@dp.callback_query_handler(lambda c: c.data.startswith("pay_ok:"))
async def pay_ok(call: types.CallbackQuery):
    uid = int(call.data.split(":")[1])

    if uid not in orders:
        await call.answer("سفارش پیدا نشد", show_alert=True)
        return

    orders[uid]["status"] = "paid"

    # پیام به مشتری
    await bot.send_message(
        uid,
        "✅ پرداخت شما تایید شد\n🍝 غذا تا ۱۵ دقیقه دیگر آماده می‌شود"
    )

    # دکمه ادامه برای ادمین
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("🍝 غذا آماده است", callback_data=f"food_ready:{uid}")
    )

    await call.message.edit_caption(
        call.message.caption + "\n\n✅ پرداخت تایید شد",
        reply_markup=kb
    )

    await call.answer("پرداخت تایید شد ✅")
    
@dp.callback_query_handler(lambda c: c.data.startswith("pay_no:"))
async def pay_no(call: types.CallbackQuery):
    uid = int(call.data.split(":")[1])

    if uid in orders:
        orders.pop(uid)

    await bot.send_message(
        uid,
        "❌ پرداخت شما تایید نشد\nدر صورت نیاز دوباره سفارش ثبت کنید"
    )

    await call.message.edit_caption(
        call.message.caption + "\n\n❌ پرداخت رد شد"
    )

    await call.answer("پرداخت رد شد ❌")

# ===================== ADMIN ACTIONS =====================
@dp.message_handler(content_types=ContentType.PHOTO)
async def receipt(message):
    uid = message.from_user.id

    if uid not in orders:
        await message.answer("❌ سفارشی برای بررسی پیدا نشد")
        return

    order = orders[uid]
    user = users[uid]

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✅ تایید پرداخت", callback_data=f"pay_ok:{uid}"),
        InlineKeyboardButton("❌ رد پرداخت", callback_data=f"pay_no:{uid}")
    )

    for admin in ADMIN_IDS:
        await bot.send_photo(
            admin,
            message.photo[-1].file_id,
            caption=(
                "🧾 فیش پرداخت کارت به کارت\n\n"
                f"👤 نام: {user['name']}\n"
                f"📞 تلفن: {user['phone']}\n"
                f"💰 مبلغ: {order['total']} تومان\n\n"
                f"📦 سفارش:\n" +
                "\n".join([f"{f} × {q}" for f, q in order["items"].items()])
            ),
            reply_markup=kb
        )

    await message.answer("⏳ فیش شما برای ادمین ارسال شد و در حال بررسی است")

@dp.callback_query_handler(lambda c: c.data.startswith("food_ready:"))
async def food_ready(call):
    uid = int(call.data.split(":")[1])
    await bot.send_message(uid, "🍽 غذای شما آماده است\n🙏 منتظر حضور شما هستیم")
    await call.answer("ارسال شد")

@dp.callback_query_handler(lambda c: c.data.startswith("close_order:"))
async def close_order(call):
    uid = int(call.data.split(":")[1])
    orders.pop(uid, None)
    carts[uid] = {}

    await bot.send_message(
        uid,
        "🙏 از اینکه ما را انتخاب کردید ممنونیم\n🌹 منتظر حضور دوباره شما هستیم"
    )
    await call.message.edit_text("✅ سفارش بسته شد")
    await call.answer()
# ================= ADMIN REPORT =================
@dp.message_handler(lambda m: m.text == "📊 گزارش ادمین")
async def report(message):
    await message.answer(
        f"""📊 گزارش
👥 کاربران: {len(users)}
🛒 سفارش‌های فعال: {len(orders)}"""
    )

# ===================== RUN =====================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

