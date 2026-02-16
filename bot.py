from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import *
import logging

logging.basicConfig(level=logging.INFO)

TOKEN = "8543932711:AAFBzavfn2MunYAvnCKWiAEisUIyEmT04XQ"
ADMIN_IDS = [289763127]

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ===================== DATA =====================
MENU = {
    "آلفردو": 450,
    "بولونز": 450,
    "پیتزا مرغ": 580,
    "پیتزا پپرونی": 580,
    "لازانیا": 580,
    "نوشابه": 50
}

CARD_NUMBER = "6219-8618-1166-9158"
CARD_OWNER = "امین آقازاده"

users = {}
carts = {}
orders = {}

# ===================== START =====================
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📱 ارسال شماره", request_contact=True))
    await message.answer("🍝 به رستوران ROMA خوش آمدید\nشماره تماس را ارسال کنید", reply_markup=kb)

# ===================== REGISTER =====================
@dp.message_handler(content_types=ContentType.CONTACT)
async def register(message: types.Message):
    uid = message.from_user.id
    users[uid] = {
        "name": message.from_user.full_name,
        "phone": message.contact.phone_number
    }
    carts[uid] = {}

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🍽 منوی غذا", "📞 تماس با ما", "📷 اینستاگرام")
    await message.answer("✅ ثبت‌نام انجام شد", reply_markup=kb)

# ===================== CONTACT =====================
@dp.message_handler(lambda m: m.text == "📞 تماس با ما")
async def contact(message: types.Message):
    await message.answer("📞 09141604866")

@dp.message_handler(lambda m: m.text == "📷 اینستاگرام")
async def insta(message: types.Message):
    await message.answer("📷 @roma.italianfoods")

# ===================== FOOD MENU =====================
@dp.message_handler(lambda m: m.text == "🍽 منوی غذا")
async def food_menu(message: types.Message):
    kb = InlineKeyboardMarkup(row_width=2)
    for food, price in MENU.items():
        kb.add(InlineKeyboardButton(f"{food} - {price}", callback_data=f"food:{food}"))
    kb.add(InlineKeyboardButton("🛒 سبد خرید", callback_data="cart"))
    await message.answer("🍽 منوی غذا:", reply_markup=kb)

# ===================== CHOOSE QTY =====================
@dp.callback_query_handler(lambda c: c.data.startswith("food:"))
async def choose_qty(call: CallbackQuery):
    food = call.data.split(":")[1]
    kb = InlineKeyboardMarkup(row_width=5)
    for i in range(1, 6):
        kb.insert(InlineKeyboardButton(str(i), callback_data=f"add:{food}:{i}"))
    kb.add(InlineKeyboardButton("⬅ بازگشت", callback_data="back_menu"))
    await call.message.edit_text(f"تعداد «{food}» را انتخاب کنید:", reply_markup=kb)

# ===================== ADD TO CART =====================
@dp.callback_query_handler(lambda c: c.data.startswith("add:"))
async def add_to_cart(call: CallbackQuery):
    _, food, qty = call.data.split(":")
    uid = call.from_user.id
    carts[uid][food] = carts[uid].get(food, 0) + int(qty)

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("➕ افزودن غذا", callback_data="back_menu"),
        InlineKeyboardButton("🛒 سبد خرید", callback_data="cart")
    )
    await call.message.edit_text("✅ به سبد خرید اضافه شد", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "back_menu")
async def back_menu(call: CallbackQuery):
    await food_menu(call.message)

# ===================== CART =====================
@dp.callback_query_handler(lambda c: c.data == "cart")
async def show_cart(call: CallbackQuery):
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
        InlineKeyboardButton("⬅ بازگشت", callback_data="back_menu")
    )
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("del:"))
async def delete_item(call: CallbackQuery):
    food = call.data.split(":")[1]
    carts[call.from_user.id].pop(food, None)
    await show_cart(call)

# ===================== CONFIRM =====================
@dp.callback_query_handler(lambda c: c.data == "confirm")
async def confirm(call: CallbackQuery):
    uid = call.from_user.id
    total = sum(MENU[f] * q for f, q in carts[uid].items())

    orders[uid] = {
        "items": carts[uid],
        "total": total,
        "method": None
    }

    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("💵 پرداخت حضوری", callback_data="pay_cash"),
        InlineKeyboardButton("💳 کارت به کارت", callback_data="pay_card"),
        InlineKeyboardButton("🚚 ارسال با پیک", callback_data="pay_delivery")
    )

    await call.message.edit_text(
        f"💰 مبلغ نهایی: {total}\nروش پرداخت را انتخاب کنید:",
        reply_markup=kb
    )

# ===================== CASH =====================
@dp.callback_query_handler(lambda c: c.data == "pay_cash")
async def pay_cash(call: CallbackQuery):
    uid = call.from_user.id
    orders[uid]["method"] = "cash"

    items = "\n".join([f"{k} × {v}" for k, v in carts[uid].items()])

    for admin in ADMIN_IDS:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🍽 غذا آماده است", callback_data=f"ready:{uid}"))
        await bot.send_message(
            admin,
            f"💵 پرداخت حضوری\n👤 {users[uid]['name']}\n📞 {users[uid]['phone']}\n\n{items}",
            reply_markup=kb
        )

    await call.message.edit_text("✅ سفارش ثبت شد\n⏳ منتظر آماده شدن غذا باشید")

# ===================== CARD =====================
@dp.callback_query_handler(lambda c: c.data == "pay_card")
async def pay_card(call: CallbackQuery):
    uid = call.from_user.id
    orders[uid]["method"] = "card"
    await call.message.edit_text(
        f"💳 کارت به کارت\n{CARD_NUMBER}\n👤 {CARD_OWNER}\n\n📸 فیش پرداختی را ارسال کنید"
    )

# ===================== DELIVERY =====================
@dp.callback_query_handler(lambda c: c.data == "pay_delivery")
async def pay_delivery(call: CallbackQuery):
    uid = call.from_user.id
    orders[uid]["method"] = "delivery"
    await call.message.edit_text(
        f"🚚 ارسال با پیک\n💳 مبلغ را پرداخت و فیش را ارسال کنید\n{CARD_NUMBER}"
    )

# ===================== RECEIVE RECEIPT =====================
@dp.message_handler(content_types=ContentType.PHOTO)
async def receive_receipt(message: types.Message):
    uid = message.from_user.id
    if uid not in orders:
        return

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✅ تایید پرداخت", callback_data=f"ok:{uid}"),
        InlineKeyboardButton("❌ رد پرداخت", callback_data=f"no:{uid}")
    )

    for admin in ADMIN_IDS:
        await bot.send_photo(
            admin,
            message.photo[-1].file_id,
            caption=f"🧾 فیش پرداخت\n👤 {users[uid]['name']}\n💰 {orders[uid]['total']}",
            reply_markup=kb
        )

    await message.answer("⏳ فیش ارسال شد، منتظر تایید")

# ===================== ADMIN =====================
@dp.callback_query_handler(lambda c: c.data.startswith("ok:"))
async def approve(call: CallbackQuery):
    uid = int(call.data.split(":")[1])
    await bot.send_message(uid, "✅ پرداخت تایید شد\n🍝 در حال آماده‌سازی")
    await call.answer("تایید شد")

@dp.callback_query_handler(lambda c: c.data.startswith("no:"))
async def reject(call: CallbackQuery):
    uid = int(call.data.split(":")[1])
    orders.pop(uid, None)
    carts[uid] = {}
    await bot.send_message(uid, "❌ پرداخت رد شد")
    await call.answer("رد شد")

# ===================== RUN =====================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
