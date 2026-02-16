from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import *
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import logging

logging.basicConfig(level=logging.INFO)

TOKEN = "8543932711:AAFBzavfn2MunYAvnCKWiAEisUIyEmT04XQ"
ADMIN_IDS = [289763127]

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

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

# ===================== STATES =====================
class RegisterState(StatesGroup):
    waiting_for_contact = State()

# ===================== START =====================
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    uid = message.from_user.id
    
    if uid in users:
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🍽 منوی غذا", "📞 تماس با ما", "📷 اینستاگرام")
        await message.answer("🍝 به رستوران ROMA خوش آمدید", reply_markup=kb)
    else:
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        button = KeyboardButton("📱 ارسال شماره", request_contact=True)
        kb.add(button)
        await message.answer(
            "🍝 به رستوران ROMA خوش آمدید\n"
            "لطفاً برای ثبت‌نام شماره تماس خود را ارسال کنید",
            reply_markup=kb
        )
        await RegisterState.waiting_for_contact.set()

# ===================== REGISTER =====================
@dp.message_handler(content_types=ContentType.CONTACT, state=RegisterState.waiting_for_contact)
async def register(message: types.Message, state: FSMContext):
    uid = message.from_user.id
    users[uid] = {
        "name": message.from_user.full_name,
        "phone": message.contact.phone_number
    }
    carts[uid] = {}
    
    await state.finish()

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🍽 منوی غذا", "📞 تماس با ما", "📷 اینستاگرام")
    await message.answer("✅ ثبت‌نام با موفقیت انجام شد", reply_markup=kb)

# ===================== CONTACT =====================
@dp.message_handler(lambda m: m.text == "📞 تماس با ما")
async def contact(message: types.Message):
    await message.answer(
        "📞 09141604866\n"
        "📍 آدرس: تهران، ...\n"
        "⏰ ساعت کاری: 12 ظهر تا 12 شب"
    )

@dp.message_handler(lambda m: m.text == "📷 اینستاگرام")
async def insta(message: types.Message):
    await message.answer(
        "📷 اینستاگرام ما:\n"
        "@roma.italianfoods\n"
        "🌐 https://instagram.com/roma.italianfoods"
    )

# ===================== FOOD MENU =====================
@dp.message_handler(lambda m: m.text == "🍽 منوی غذا")
async def food_menu(message: types.Message):
    uid = message.from_user.id
    
    if uid not in users:
        await start(message)
        return
    
    text = "🍽 منوی غذا:\n\n"
    for food, price in MENU.items():
        text += f"• {food}: {price} تومان\n"
    
    kb = InlineKeyboardMarkup(row_width=1)  # تغییر به 1 دکمه در هر ردیف برای نمایش بهتر
    
    for food, price in MENU.items():
        # هر غذا یک دکمه جداگانه دارد که با کلیک روی آن مستقیماً به سبد خرید اضافه می‌شود
        button_text = f"➕ {food} - {price} تومان"
        kb.add(InlineKeyboardButton(button_text, callback_data=f"add_to_cart:{food}"))
    
    # دکمه مشاهده سبد خرید
    kb.add(InlineKeyboardButton("🛒 مشاهده سبد خرید", callback_data="cart"))
    
    await message.answer(text, reply_markup=kb)

# ===================== DIRECT ADD TO CART =====================
@dp.callback_query_handler(lambda c: c.data.startswith("add_to_cart:"))
async def direct_add_to_cart(call: CallbackQuery):
    food = call.data.split(":")[1]
    uid = call.from_user.id
    
    # اضافه کردن مستقیم به سبد خرید (پیش‌فرض تعداد 1)
    if food not in carts[uid]:
        carts[uid][food] = 0
    carts[uid][food] += 1
    
    # محاسبه تعداد کل آیتم‌ها و قیمت کل
    total_items = sum(carts[uid].values())
    total_price = sum(MENU[f] * q for f, q in carts[uid].items())
    
    # ایجاد کیبورد برای ادامه خرید
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("➕ ادامه خرید", callback_data="back_to_menu"),
        InlineKeyboardButton("🛒 سبد خرید", callback_data="cart"),
        InlineKeyboardButton("📦 تغییر تعداد", callback_data=f"change_qty:{food}")  # دکمه تغییر تعداد
    )
    
    await call.message.edit_text(
        f"✅ {food} به سبد خرید اضافه شد!\n\n"
        f"🛒 وضعیت سبد خرید:\n"
        f"📦 تعداد آیتم‌ها: {total_items}\n"
        f"💰 جمع کل: {total_price} تومان",
        reply_markup=kb
    )

# ===================== CHANGE QUANTITY =====================
@dp.callback_query_handler(lambda c: c.data.startswith("change_qty:"))
async def change_quantity(call: CallbackQuery):
    food = call.data.split(":")[1]
    uid = call.from_user.id
    
    current_qty = carts[uid].get(food, 1)
    
    kb = InlineKeyboardMarkup(row_width=3)
    
    # دکمه‌های افزایش و کاهش تعداد
    buttons = []
    for i in range(1, 6):
        buttons.append(InlineKeyboardButton(str(i), callback_data=f"set_qty:{food}:{i}"))
    kb.add(*buttons)
    
    # دکمه‌های کمکی
    kb.add(
        InlineKeyboardButton("➖ کاهش", callback_data=f"decrease_qty:{food}"),
        InlineKeyboardButton("➕ افزایش", callback_data=f"increase_qty:{food}"),
        InlineKeyboardButton("❌ حذف", callback_data=f"del:{food}")
    )
    
    kb.add(InlineKeyboardButton("🔙 بازگشت به سبد خرید", callback_data="cart"))
    
    await call.message.edit_text(
        f"📦 {food}\n"
        f"تعداد فعلی: {current_qty}\n"
        f"قیمت واحد: {MENU[food]} تومان\n"
        f"قیمت کل: {MENU[food] * current_qty} تومان\n\n"
        f"تعداد جدید را انتخاب کنید:",
        reply_markup=kb
    )

@dp.callback_query_handler(lambda c: c.data.startswith("set_qty:"))
async def set_quantity(call: CallbackQuery):
    _, food, qty = call.data.split(":")
    uid = call.from_user.id
    
    carts[uid][food] = int(qty)
    
    # نمایش سبد خرید به‌روز شده
    await show_cart(call)

@dp.callback_query_handler(lambda c: c.data.startswith("increase_qty:"))
async def increase_quantity(call: CallbackQuery):
    food = call.data.split(":")[1]
    uid = call.from_user.id
    
    carts[uid][food] = carts[uid].get(food, 1) + 1
    
    # نمایش دوباره صفحه تغییر تعداد
    await change_quantity(call)

@dp.callback_query_handler(lambda c: c.data.startswith("decrease_qty:"))
async def decrease_quantity(call: CallbackQuery):
    food = call.data.split(":")[1]
    uid = call.from_user.id
    
    if carts[uid].get(food, 1) > 1:
        carts[uid][food] -= 1
    else:
        # اگر تعداد به 1 برسد و کاربر کاهش دهد، آیتم حذف می‌شود
        await delete_item(call)
        return
    
    # نمایش دوباره صفحه تغییر تعداد
    await change_quantity(call)

# ===================== BACK TO MENU =====================
@dp.callback_query_handler(lambda c: c.data == "back_to_menu")
async def back_to_menu(call: CallbackQuery):
    await food_menu(call.message)

# ===================== CART =====================
@dp.callback_query_handler(lambda c: c.data == "cart")
async def show_cart(call: CallbackQuery):
    uid = call.from_user.id
    
    if not carts.get(uid) or not carts[uid]:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🍽 مشاهده منو", callback_data="back_to_menu"))
        await call.message.edit_text("🛒 سبد خرید شما خالی است!", reply_markup=kb)
        return
    
    total = 0
    text = "🛒 سبد خرید شما:\n\n"
    kb = InlineKeyboardMarkup(row_width=1)
    
    for food, qty in carts[uid].items():
        price = MENU[food] * qty
        total += price
        text += f"• {food} × {qty} = {price} تومان\n"
        # دکمه تغییر تعداد برای هر آیتم
        kb.add(InlineKeyboardButton(f"📦 تغییر تعداد {food}", callback_data=f"change_qty:{food}"))
    
    text += f"\n💰 جمع کل: {total} تومان"
    
    kb.add(
        InlineKeyboardButton("✅ نهایی کردن سفارش", callback_data="confirm"),
        InlineKeyboardButton("➕ اضافه کردن غذا", callback_data="back_to_menu"),
        InlineKeyboardButton("🗑 خالی کردن سبد", callback_data="clear_cart")
    )
    
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("del:"))
async def delete_item(call: CallbackQuery):
    food = call.data.split(":")[1]
    uid = call.from_user.id
    
    if food in carts[uid]:
        del carts[uid][food]
    
    await show_cart(call)

@dp.callback_query_handler(lambda c: c.data == "clear_cart")
async def clear_cart(call: CallbackQuery):
    uid = call.from_user.id
    carts[uid] = {}
    
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🍽 مشاهده منو", callback_data="back_to_menu"))
    
    await call.message.edit_text("🗑 سبد خرید خالی شد!", reply_markup=kb)

# ===================== CONFIRM =====================
@dp.callback_query_handler(lambda c: c.data == "confirm")
async def confirm(call: CallbackQuery):
    uid = call.from_user.id
    total = sum(MENU[f] * q for f, q in carts[uid].items())
    
    orders[uid] = {
        "items": carts[uid].copy(),
        "total": total,
        "method": None
    }
    
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("💵 پرداخت حضوری", callback_data="pay_cash"),
        InlineKeyboardButton("💳 کارت به کارت", callback_data="pay_card"),
        InlineKeyboardButton("🚚 ارسال با پیک", callback_data="pay_delivery"),
        InlineKeyboardButton("🔙 بازگشت به سبد خرید", callback_data="cart")
    )
    
    await call.message.edit_text(
        f"💰 مبلغ قابل پرداخت: {total} تومان\n\n"
        f"لطفاً روش پرداخت را انتخاب کنید:",
        reply_markup=kb
    )

# ===================== PAYMENT METHODS =====================
@dp.callback_query_handler(lambda c: c.data == "pay_cash")
async def pay_cash(call: CallbackQuery):
    uid = call.from_user.id
    orders[uid]["method"] = "cash"
    
    items_text = "\n".join([f"• {k} × {v}" for k, v in carts[uid].items()])
    
    for admin in ADMIN_IDS:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("✅ غذا آماده شد", callback_data=f"ready:{uid}"))
        
        await bot.send_message(
            admin,
            f"💰 سفارش جدید - پرداخت حضوری\n\n"
            f"👤 نام: {users[uid]['name']}\n"
            f"📞 شماره: {users[uid]['phone']}\n\n"
            f"📝 سفارش:\n{items_text}\n\n"
            f"💰 مبلغ: {orders[uid]['total']} تومان",
            reply_markup=kb
        )
    
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🏠 بازگشت به منو", callback_data="back_to_menu"))
    
    await call.message.edit_text(
        "✅ سفارش شما با موفقیت ثبت شد!\n\n"
        "⏳ منتظر تأیید رستوران باشید\n"
        "🍝 غذای شما در حال آماده‌سازی است",
        reply_markup=kb
    )
    
    carts[uid] = {}

@dp.callback_query_handler(lambda c: c.data == "pay_card")
async def pay_card(call: CallbackQuery):
    uid = call.from_user.id
    orders[uid]["method"] = "card"
    
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✅ ارسال فیش", callback_data="send_receipt"))
    
    await call.message.edit_text(
        f"💳 اطلاعات کارت:\n\n"
        f"🆔 شماره کارت: {CARD_NUMBER}\n"
        f"👤 به نام: {CARD_OWNER}\n\n"
        f"💰 مبلغ: {orders[uid]['total']} تومان\n\n"
        f"📸 لطفاً پس از واریز، تصویر فیش را ارسال کنید",
        reply_markup=kb
    )

@dp.callback_query_handler(lambda c: c.data == "pay_delivery")
async def pay_delivery(call: CallbackQuery):
    uid = call.from_user.id
    orders[uid]["method"] = "delivery"
    
    await call.message.edit_text(
        f"🚚 ارسال با پیک\n\n"
        f"لطفاً برای تکمیل سفارش:\n"
        f"1️⃣ مبلغ {orders[uid]['total']} تومان را به کارت زیر واریز کنید\n"
        f"2️⃣ تصویر فیش را ارسال کنید\n\n"
        f"💳 {CARD_NUMBER}\n"
        f"👤 {CARD_OWNER}"
    )

@dp.callback_query_handler(lambda c: c.data == "send_receipt")
async def send_receipt(call: CallbackQuery):
    await call.message.edit_text(
        "📸 لطفاً تصویر فیش پرداخت را ارسال کنید"
    )

# ===================== RECEIVE RECEIPT =====================
@dp.message_handler(content_types=ContentType.PHOTO)
async def receive_receipt(message: types.Message):
    uid = message.from_user.id
    
    if uid not in orders:
        await message.answer("❌ شما سفارش فعالی ندارید")
        return
    
    items_text = "\n".join([f"• {k} × {v}" for k, v in orders[uid]['items'].items()])
    
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ تأیید", callback_data=f"approve_payment:{uid}"),
        InlineKeyboardButton("❌ رد", callback_data=f"reject_payment:{uid}")
    )
    
    for admin in ADMIN_IDS:
        await bot.send_photo(
            admin,
            message.photo[-1].file_id,
            caption=
            f"🧾 فیش پرداخت جدید\n\n"
            f"👤 نام: {users[uid]['name']}\n"
            f"📞 شماره: {users[uid]['phone']}\n"
            f"💰 مبلغ: {orders[uid]['total']} تومان\n"
            f"💳 روش: {orders[uid]['method']}\n\n"
            f"📝 سفارش:\n{items_text}",
            reply_markup=kb
        )
    
    await message.answer("✅ فیش پرداخت ارسال شد\n⏳ منتظر تأیید ادمین باشید")

# ===================== ADMIN APPROVALS =====================
@dp.callback_query_handler(lambda c: c.data.startswith("approve_payment:"))
async def approve_payment(call: CallbackQuery):
    uid = int(call.data.split(":")[1])
    
    await bot.send_message(
        uid,
        "✅ پرداخت شما تأیید شد!\n\n"
        "🍝 سفارش شما در حال آماده‌سازی است"
    )
    
    await call.message.edit_caption(
        call.message.caption + "\n\n✅ تأیید شده توسط ادمین"
    )
    await call.answer("✅ پرداخت تأیید شد")

@dp.callback_query_handler(lambda c: c.data.startswith("reject_payment:"))
async def reject_payment(call: CallbackQuery):
    uid = int(call.data.split(":")[1])
    
    await bot.send_message(
        uid,
        "❌ پرداخت شما رد شد!\n"
        "لطفاً مجدداً تلاش کنید یا با پشتیبانی تماس بگیرید"
    )
    
    await call.message.edit_caption(
        call.message.caption + "\n\n❌ رد شده توسط ادمین"
    )
    await call.answer("❌ پرداخت رد شد")

@dp.callback_query_handler(lambda c: c.data.startswith("ready:"))
async def order_ready(call: CallbackQuery):
    uid = int(call.data.split(":")[1])
    
    await bot.send_message(
        uid,
        "✅ سفارش شما آماده است!\n\n"
        "🍝 می‌توانید برای تحویل سفارش خود مراجعه کنید"
    )
    
    await call.answer("✅ اطلاع‌رسانی شد")

# ===================== HELPERS =====================
@dp.message_handler(commands=["help"])
async def help_command(message: types.Message):
    await message.answer(
        "🤖 راهنمای ربات:\n\n"
        "• /start - شروع مجدد\n"
        "• منوی غذا - مشاهده منو و سفارش\n"
        "• تماس با ما - اطلاعات تماس\n"
        "• اینستاگرام - صفحه اینستاگرام\n\n"
        "برای هر سوال با پشتیبانی تماس بگیرید: 09141604866"
    )

# ===================== FALLBACK =====================
@dp.message_handler()
async def fallback(message: types.Message):
    if message.from_user.id not in users:
        await start(message)
    else:
        await message.answer(
            "❌ دستور نامعتبر!\n"
            "لطفاً از دکمه‌های زیر استفاده کنید"
        )

# ===================== RUN =====================
if __name__ == "__main__":
    print("🤖 ربات در حال اجرا است...")
    executor.start_polling(dp, skip_updates=True)
