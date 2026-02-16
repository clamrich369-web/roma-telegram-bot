from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import *
from datetime import date

TOKEN = "8543932711:AAFBzavfn2MunYAvnCKWiAEisUIyEmT04XQ"
ADMIN_IDS = [289763127]

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

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

# ================= START =================
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📱 ارسال شماره تلفن", request_contact=True))
    await message.answer("🍝 به ROMA خوش آمدید\nشماره تلفن خود را ارسال کنید", reply_markup=kb)

# ================= REGISTER =================
@dp.message_handler(content_types=ContentType.CONTACT)
async def register(message: types.Message):
    uid = message.from_user.id
    users[uid] = {
        "name": message.from_user.full_name,
        "phone": message.contact.phone_number
    }
    carts[uid] = {}
    stats[uid] = {"orders": 0, "total": 0, "ratings": []}
    await show_main_menu(message)

# ================= MAIN MENU =================
async def show_main_menu(message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🍽 منوی غذا", "✍️ انتقاد و پیشنهاد")
    kb.add("📞 تماس با ما", "📷 اینستاگرام")
    if message.from_user.id in ADMIN_IDS:
        kb.add("📊 گزارش ادمین")
    await message.answer("انتخاب کنید:", reply_markup=kb)

# ================= MENU =================
@dp.message_handler(lambda m: m.text == "🍽 منوی غذا")
async def show_menu(message):
    kb = InlineKeyboardMarkup(row_width=2)
    for food, price in MENU.items():
        kb.add(InlineKeyboardButton(f"{food} - {price}", callback_data=f"food:{food}"))
    kb.add(InlineKeyboardButton("🛒 سبد خرید", callback_data="cart"))
    await message.answer("غذای مورد نظر را انتخاب کنید:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("food:"))
async def choose_qty(call: CallbackQuery):
    food = call.data.split(":")[1]
    kb = InlineKeyboardMarkup()
    for i in range(1, 6):
        kb.add(InlineKeyboardButton(str(i), callback_data=f"add:{food}:{i}"))
    await call.message.edit_text("تعداد را انتخاب کنید:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("add:"))
async def add_cart(call: CallbackQuery):
    _, food, qty = call.data.split(":")
    uid = call.from_user.id
    carts[uid][food] = carts[uid].get(food, 0) + int(qty)
    await call.message.edit_text("✅ به سبد خرید اضافه شد")

# ================= CART =================
@dp.callback_query_handler(lambda c: c.data == "cart")
async def cart(call: CallbackQuery):
    uid = call.from_user.id
    if not carts[uid]:
        await call.message.edit_text("❌ سبد خرید خالی است")
        return

    total = 0
    text = "🛒 سبد خرید\n\n"
    for f, q in carts[uid].items():
        total += MENU[f] * q
        text += f"{f} × {q}\n"

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✅ تایید سفارش", callback_data="confirm"))
    await call.message.edit_text(text + f"\n💰 {total}", reply_markup=kb)

# ================= CONFIRM =================
@dp.callback_query_handler(lambda c: c.data == "confirm")
async def confirm(call: CallbackQuery):
    uid = call.from_user.id
    total = sum(MENU[f] * q for f, q in carts[uid].items())
    orders[uid] = {"items": carts[uid], "total": total}

    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("💵 پرداخت حضوری", callback_data="pay_cash"),
        InlineKeyboardButton("💳 کارت به کارت", callback_data="pay_card"),
        InlineKeyboardButton("🚚 ارسال به پیک", callback_data="pay_delivery")
    )

    await call.message.edit_text("روش پرداخت را انتخاب کنید:", reply_markup=kb)

# ================= PAY CASH =================
@dp.callback_query_handler(lambda c: c.data == "pay_cash")
async def pay_cash(call: CallbackQuery):
    uid = call.from_user.id
    for admin in ADMIN_IDS:
        await bot.send_message(admin, f"💵 پرداخت حضوری\n👤 {users[uid]['name']}")
    await call.message.edit_text("✅ سفارش ثبت شد")

# ================= PAY CARD / DELIVERY =================
@dp.callback_query_handler(lambda c: c.data in ["pay_card", "pay_delivery"])
async def pay_card(call: CallbackQuery):
    uid = call.from_user.id
    await call.message.edit_text(
        f"💳 کارت به کارت\n{CARD_NUMBER}\n{CARD_OWNER}\n📸 فیش را ارسال کنید"
    )

# ================= RECEIPT =================
@dp.message_handler(content_types=ContentType.PHOTO)
async def receive_receipt(message: types.Message):
    uid = message.from_user.id
    if uid not in orders:
        return

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✅ تایید", callback_data=f"approve:{uid}"),
        InlineKeyboardButton("❌ رد", callback_data=f"reject:{uid}")
    )

    for admin in ADMIN_IDS:
        await bot.send_photo(
            admin,
            message.photo[-1].file_id,
            caption="🧾 فیش پرداخت",
            reply_markup=kb
        )

    await message.answer("⏳ فیش ارسال شد")

# ================= APPROVE / REJECT =================
@dp.callback_query_handler(lambda c: c.data.startswith("approve:"))
async def approve(call: CallbackQuery):
    uid = int(call.data.split(":")[1])
    await bot.send_message(uid, "✅ پرداخت تایید شد")

@dp.callback_query_handler(lambda c: c.data.startswith("reject:"))
async def reject(call: CallbackQuery):
    uid = int(call.data.split(":")[1])
    await bot.send_message(uid, "❌ پرداخت رد شد")

# ================= RUN =================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
