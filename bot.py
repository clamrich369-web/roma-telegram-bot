from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import *
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import logging
import json
import os

logging.basicConfig(level=logging.INFO)

TOKEN = "8543932711:AAFBzavfn2MunYAvnCKWiAEisUIyEmT04XQ"
ADMIN_IDS = [289763127]

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ===================== DATA FILES =====================
USERS_FILE = "users.json"
CARTS_FILE = "carts.json"
ORDERS_FILE = "orders.json"

# ===================== LOAD/SAVE FUNCTIONS =====================
def load_data():
    global users, carts, orders
    
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users = json.load(f)
            users = {int(k): v for k, v in users.items()}
    else:
        users = {}
    
    if os.path.exists(CARTS_FILE):
        with open(CARTS_FILE, 'r', encoding='utf-8') as f:
            carts = json.load(f)
            carts = {int(k): v for k, v in carts.items()}
    else:
        carts = {}
    
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
            orders = json.load(f)
            orders = {int(k): v for k, v in orders.items()}
    else:
        orders = {}

def save_users():
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def save_carts():
    with open(CARTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(carts, f, ensure_ascii=False, indent=2)

def save_orders():
    with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

load_data()

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

# ===================== STATES =====================
class RegisterState(StatesGroup):
    waiting_for_contact = State()

class PaymentState(StatesGroup):
    waiting_for_receipt = State()  # منتظر ماندن برای دریافت فیش

# ===================== START =====================
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    uid = message.from_user.id
    
    if str(uid) in users or uid in users:
        if uid not in carts:
            carts[uid] = {}
            save_carts()
            
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
        "phone": message.contact.phone_number,
        "register_date": str(message.date)
    }
    carts[uid] = {}
    
    save_users()
    save_carts()
    
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
    
    if str(uid) not in users and uid not in users:
        await start(message)
        return
    
    if uid not in carts:
        carts[uid] = {}
        save_carts()
    
    text = "🍽 منوی غذا:\n\n"
    for food, price in MENU.items():
        text += f"• {food}: {price} تومان\n"
    
    kb = InlineKeyboardMarkup(row_width=1)
    
    for food, price in MENU.items():
        button_text = f"➕ {food} - {price} تومان"
        kb.add(InlineKeyboardButton(button_text, callback_data=f"add_to_cart:{food}"))
    
    if carts[uid]:
        total_items = sum(carts[uid].values())
        total_price = sum(MENU[f] * q for f, q in carts[uid].items())
        kb.add(InlineKeyboardButton(f"🛒 سبد خرید ({total_items} آیتم - {total_price} تومان)", callback_data="cart"))
    else:
        kb.add(InlineKeyboardButton("🛒 سبد خرید (خالی)", callback_data="cart"))
    
    await message.answer(text, reply_markup=kb)

# ===================== DIRECT ADD TO CART =====================
@dp.callback_query_handler(lambda c: c.data.startswith("add_to_cart:"))
async def direct_add_to_cart(call: CallbackQuery):
    food = call.data.split(":")[1]
    uid = call.from_user.id
    
    if uid not in carts:
        carts[uid] = {}
    
    if food not in carts[uid]:
        carts[uid][food] = 0
    carts[uid][food] += 1
    
    save_carts()
    
    total_items = sum(carts[uid].values())
    total_price = sum(MENU[f] * q for f, q in carts[uid].items())
    
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("➕ ادامه خرید", callback_data="back_to_menu"),
        InlineKeyboardButton("🛒 سبد خرید", callback_data="cart"),
        InlineKeyboardButton("📦 تغییر تعداد", callback_data=f"change_qty:{food}")
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
    
    if uid not in carts:
        carts[uid] = {}
        save_carts()
    
    current_qty = carts[uid].get(food, 1)
    
    kb = InlineKeyboardMarkup(row_width=3)
    
    buttons = []
    for i in range(1, 6):
        if i == current_qty:
            buttons.append(InlineKeyboardButton(f"✅ {i}", callback_data=f"set_qty:{food}:{i}"))
        else:
            buttons.append(InlineKeyboardButton(str(i), callback_data=f"set_qty:{food}:{i}"))
    kb.add(*buttons)
    
    kb.add(
        InlineKeyboardButton("➖ کاهش", callback_data=f"decrease_qty:{food}"),
        InlineKeyboardButton("➕ افزایش", callback_data=f"increase_qty:{food}"),
        InlineKeyboardButton("❌ حذف از سبد", callback_data=f"del:{food}")
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
    
    if uid not in carts:
        carts[uid] = {}
    
    carts[uid][food] = int(qty)
    save_carts()
    
    await show_cart(call)

@dp.callback_query_handler(lambda c: c.data.startswith("increase_qty:"))
async def increase_quantity(call: CallbackQuery):
    food = call.data.split(":")[1]
    uid = call.from_user.id
    
    if uid not in carts:
        carts[uid] = {}
    
    carts[uid][food] = carts[uid].get(food, 1) + 1
    save_carts()
    
    await change_quantity(call)

@dp.callback_query_handler(lambda c: c.data.startswith("decrease_qty:"))
async def decrease_quantity(call: CallbackQuery):
    food = call.data.split(":")[1]
    uid = call.from_user.id
    
    if uid not in carts:
        carts[uid] = {}
    
    if carts[uid].get(food, 1) > 1:
        carts[uid][food] -= 1
        save_carts()
        await change_quantity(call)
    else:
        await delete_item(call)

# ===================== BACK TO MENU =====================
@dp.callback_query_handler(lambda c: c.data == "back_to_menu")
async def back_to_menu(call: CallbackQuery):
    uid = call.from_user.id
    
    text = "🍽 منوی غذا:\n\n"
    for food, price in MENU.items():
        text += f"• {food}: {price} تومان\n"
    
    kb = InlineKeyboardMarkup(row_width=1)
    
    for food, price in MENU.items():
        button_text = f"➕ {food} - {price} تومان"
        kb.add(InlineKeyboardButton(button_text, callback_data=f"add_to_cart:{food}"))
    
    if uid in carts and carts[uid]:
        total_items = sum(carts[uid].values())
        total_price = sum(MENU[f] * q for f, q in carts[uid].items())
        kb.add(InlineKeyboardButton(f"🛒 سبد خرید ({total_items} آیتم - {total_price} تومان)", callback_data="cart"))
    else:
        kb.add(InlineKeyboardButton("🛒 سبد خرید (خالی)", callback_data="cart"))
    
    await call.message.edit_text(text, reply_markup=kb)

# ===================== CART =====================
@dp.callback_query_handler(lambda c: c.data == "cart")
async def show_cart(call: CallbackQuery):
    uid = call.from_user.id
    
    if uid not in carts:
        carts[uid] = {}
        save_carts()
    
    if not carts[uid]:
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
    
    if uid in carts and food in carts[uid]:
        del carts[uid][food]
        save_carts()
    
    await show_cart(call)

@dp.callback_query_handler(lambda c: c.data == "clear_cart")
async def clear_cart(call: CallbackQuery):
    uid = call.from_user.id
    carts[uid] = {}
    save_carts()
    
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🍽 مشاهده منو", callback_data="back_to_menu"))
    
    await call.message.edit_text("🗑 سبد خرید خالی شد!", reply_markup=kb)

# ===================== CONFIRM =====================
@dp.callback_query_handler(lambda c: c.data == "confirm")
async def confirm(call: CallbackQuery):
    uid = call.from_user.id
    
    if uid not in carts or not carts[uid]:
        await call.message.edit_text("❌ سبد خرید شما خالی است!")
        return
    
    total = sum(MENU[f] * q for f, q in carts[uid].items())
    
    orders[uid] = {
        "items": carts[uid].copy(),
        "total": total,
        "method": None,
        "status": "pending",  # وضعیت سفارش: pending, paid, preparing, ready, delivered
        "date": str(call.message.date)
    }
    save_orders()
    
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
    
    if uid not in orders:
        await call.message.edit_text("❌ سفارشی یافت نشد!")
        return
    
    orders[uid]["method"] = "cash"
    orders[uid]["status"] = "waiting_for_approval"
    save_orders()
    
    items_text = "\n".join([f"• {k} × {v}" for k, v in carts[uid].items()])
    
    # ارسال به ادمین
    for admin in ADMIN_IDS:
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅ تأیید سفارش", callback_data=f"approve_order:{uid}"),
            InlineKeyboardButton("❌ رد سفارش", callback_data=f"reject_order:{uid}")
        )
        
        await bot.send_message(
            admin,
            f"💰 سفارش جدید - پرداخت حضوری\n\n"
            f"👤 نام: {users[uid]['name']}\n"
            f"📞 شماره: {users[uid]['phone']}\n"
            f"🆔 آیدی: {uid}\n\n"
            f"📝 سفارش:\n{items_text}\n\n"
            f"💰 مبلغ: {orders[uid]['total']} تومان",
            reply_markup=kb
        )
    
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🏠 بازگشت به منو", callback_data="back_to_menu"))
    
    await call.message.edit_text(
        "✅ سفارش شما با موفقیت ثبت شد!\n\n"
        "⏳ در انتظار تأیید رستوران\n"
        "🍝 پس از تأیید، غذای شما آماده خواهد شد",
        reply_markup=kb
    )
    
    # پاک کردن سبد خرید
    carts[uid] = {}
    save_carts()

@dp.callback_query_handler(lambda c: c.data == "pay_card")
async def pay_card(call: CallbackQuery, state: FSMContext):
    uid = call.from_user.id
    
    if uid not in orders:
        await call.message.edit_text("❌ سفارشی یافت نشد!")
        return
    
    orders[uid]["method"] = "card"
    orders[uid]["status"] = "waiting_for_payment"
    save_orders()
    
    # تنظیم حالت برای دریافت فیش
    await state.set_state(PaymentState.waiting_for_receipt)
    # ذخیره موقت اینکه این کاربر برای کدام سفارش فیش می‌فرستد
    await state.update_data(order_uid=uid)
    
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("❌ انصراف", callback_data="cancel_payment"))
    
    await call.message.edit_text(
        f"💳 پرداخت کارت به کارت\n\n"
        f"🏦 اطلاعات کارت:\n"
        f"💳 شماره کارت: {CARD_NUMBER}\n"
        f"👤 به نام: {CARD_OWNER}\n\n"
        f"💰 مبلغ قابل پرداخت: {orders[uid]['total']} تومان\n\n"
        f"📸 لطفاً پس از واریز، تصویر فیش پرداخت را ارسال کنید.\n"
        f"⚠️ حتماً رسید پرداخت را به وضوح ارسال نمایید.",
        reply_markup=kb
    )

@dp.callback_query_handler(lambda c: c.data == "pay_delivery")
async def pay_delivery(call: CallbackQuery, state: FSMContext):
    uid = call.from_user.id
    
    if uid not in orders:
        await call.message.edit_text("❌ سفارشی یافت نشد!")
        return
    
    orders[uid]["method"] = "delivery"
    orders[uid]["status"] = "waiting_for_payment"
    save_orders()
    
    # تنظیم حالت برای دریافت فیش
    await state.set_state(PaymentState.waiting_for_receipt)
    await state.update_data(order_uid=uid)
    
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("❌ انصراف", callback_data="cancel_payment"))
    
    await call.message.edit_text(
        f"🚚 ارسال با پیک\n\n"
        f"برای ارسال سفارش با پیک:\n\n"
        f"1️⃣ مبلغ {orders[uid]['total']} تومان را به کارت زیر واریز کنید:\n"
        f"💳 {CARD_NUMBER}\n"
        f"👤 {CARD_OWNER}\n\n"
        f"2️⃣ تصویر فیش پرداخت را ارسال کنید\n"
        f"3️⃣ آدرس دقیق خود را وارد کنید\n\n"
        f"📸 لطفاً پس از واریز، تصویر فیش را ارسال کنید:",
        reply_markup=kb
    )

@dp.callback_query_handler(lambda c: c.data == "cancel_payment", state=PaymentState.waiting_for_receipt)
async def cancel_payment(call: CallbackQuery, state: FSMContext):
    await state.finish()
    await call.message.edit_text(
        "❌ پرداخت لغو شد.\n"
        "می‌توانید از منوی اصلی دوباره اقدام کنید."
    )

# ===================== RECEIVE RECEIPT =====================
@dp.message_handler(content_types=ContentType.PHOTO, state=PaymentState.waiting_for_receipt)
async def receive_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    uid = message.from_user.id
    order_uid = data.get('order_uid')
    
    if not order_uid or order_uid != uid:
        await message.answer("❌ خطا در شناسایی سفارش!")
        await state.finish()
        return
    
    if uid not in orders:
        await message.answer("❌ سفارشی یافت نشد!")
        await state.finish()
        return
    
    orders[uid]["status"] = "payment_received"
    save_orders()
    
    items_text = "\n".join([f"• {k} × {v}" for k, v in orders[uid]['items'].items()])
    
    # ارسال فیش به ادمین
    for admin in ADMIN_IDS:
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅ تأیید پرداخت", callback_data=f"approve_payment:{uid}"),
            InlineKeyboardButton("❌ رد پرداخت", callback_data=f"reject_payment:{uid}")
        )
        
        caption = (
            f"🧾 فیش پرداخت جدید\n\n"
            f"👤 نام: {users[uid]['name']}\n"
            f"📞 شماره: {users[uid]['phone']}\n"
            f"🆔 آیدی: {uid}\n"
            f"💰 مبلغ: {orders[uid]['total']} تومان\n"
            f"💳 روش: {orders[uid]['method']}\n\n"
            f"📝 سفارش:\n{items_text}"
        )
        
        await bot.send_photo(
            admin,
            message.photo[-1].file_id,
            caption=caption,
            reply_markup=kb
        )
    
    await state.finish()
    
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🏠 بازگشت به منو", callback_data="back_to_menu"))
    
    await message.answer(
        "✅ فیش پرداخت با موفقیت ارسال شد!\n\n"
        "⏳ در انتظار تأیید ادمین\n"
        "📍 پس از تأیید، سفارش شما آماده خواهد شد",
        reply_markup=kb
    )

# ===================== RECEIVE ADDRESS FOR DELIVERY =====================
@dp.message_handler(lambda m: m.text, state=PaymentState.waiting_for_receipt)
async def receive_address(message: types.Message, state: FSMContext):
    # اگر کاربر متن ارسال کرد (مثلاً آدرس) ولی هنوز فیش رو نفرستاده
    await message.answer(
        "❌ لطفاً ابتدا تصویر فیش پرداخت را ارسال کنید.\n"
        "اگر می‌خواهید انصراف دهید، دکمه زیر را بزنید:",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("❌ انصراف", callback_data="cancel_payment")
        )
    )

# ===================== ADMIN APPROVALS =====================
@dp.callback_query_handler(lambda c: c.data.startswith("approve_order:"))
async def approve_order(call: CallbackQuery):
    uid = int(call.data.split(":")[1])
    
    if uid in orders:
        orders[uid]["status"] = "approved"
        save_orders()
    
    await bot.send_message(
        uid,
        "✅ سفارش شما تأیید شد!\n\n"
        "🍝 در حال آماده‌سازی غذا\n"
        "⏳ لطفاً منتظر بمانید"
    )
    
    await call.message.edit_text(
        call.message.text + "\n\n✅ سفارش تأیید شد"
    )
    await call.answer("✅ سفارش تأیید شد")

@dp.callback_query_handler(lambda c: c.data.startswith("reject_order:"))
async def reject_order(call: CallbackQuery):
    uid = int(call.data.split(":")[1])
    
    if uid in orders:
        orders[uid]["status"] = "rejected"
        save_orders()
    
    await bot.send_message(
        uid,
        "❌ متأسفانه سفارش شما رد شد!\n"
        "لطفاً با پشتیبانی تماس بگیرید: 09141604866"
    )
    
    await call.message.edit_text(
        call.message.text + "\n\n❌ سفارش رد شد"
    )
    await call.answer("❌ سفارش رد شد")

@dp.callback_query_handler(lambda c: c.data.startswith("approve_payment:"))
async def approve_payment(call: CallbackQuery):
    uid = int(call.data.split(":")[1])
    
    if uid in orders:
        orders[uid]["status"] = "paid"
        save_orders()
    
    await bot.send_message(
        uid,
        "✅ پرداخت شما تأیید شد!\n\n"
        "🍝 سفارش شما در حال آماده‌سازی است\n"
        "⏳ لطفاً منتظر بمانید"
    )
    
    await call.message.edit_caption(
        call.message.caption + "\n\n✅ پرداخت تأیید شد"
    )
    await call.answer("✅ پرداخت تأیید شد")

@dp.callback_query_handler(lambda c: c.data.startswith("reject_payment:"))
async def reject_payment(call: CallbackQuery):
    uid = int(call.data.split(":")[1])
    
    if uid in orders:
        orders[uid]["status"] = "payment_rejected"
        save_orders()
    
    await bot.send_message(
        uid,
        "❌ پرداخت شما رد شد!\n\n"
        "💳 لطفاً مجدداً تلاش کنید:\n"
        f"{CARD_NUMBER}\n"
        f"{CARD_OWNER}\n\n"
        "یا با پشتیبانی تماس بگیرید: 09141604866"
    )
    
    await call.message.edit_caption(
        call.message.caption + "\n\n❌ پرداخت رد شد"
    )
    await call.answer("❌ پرداخت رد شد")

@dp.callback_query_handler(lambda c: c.data.startswith("ready:"))
async def order_ready(call: CallbackQuery):
    uid = int(call.data.split(":")[1])
    
    if uid in orders:
        orders[uid]["status"] = "ready"
        save_orders()
    
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

@dp.message_handler(commands=["status"])
async def order_status(message: types.Message):
    uid = message.from_user.id
    
    if uid in orders:
        status_text = {
            "pending": "⏳ در انتظار انتخاب روش پرداخت",
            "waiting_for_payment": "💰 در انتظار پرداخت",
            "payment_received": "📸 فیش ارسال شده - در انتظار تأیید",
            "paid": "✅ پرداخت تأیید شده",
            "approved": "✅ سفارش تأیید شده",
            "preparing": "🍝 در حال آماده‌سازی",
            "ready": "✅ آماده تحویل",
            "delivered": "🚚 تحویل داده شد",
            "rejected": "❌ رد شده",
            "payment_rejected": "❌ پرداخت رد شد"
        }
        
        status = orders[uid].get("status", "pending")
        text = status_text.get(status, "وضعیت نامشخص")
        
        await message.answer(f"📊 وضعیت سفارش شما: {text}")
    else:
        await message.answer("❌ شما سفارش فعالی ندارید")

# ===================== FALLBACK =====================
@dp.message_handler()
async def fallback(message: types.Message):
    uid = message.from_user.id
    
    if str(uid) not in users and uid not in users:
        await start(message)
    else:
        await message.answer(
            "❌ دستور نامعتبر!\n"
            "لطفاً از دکمه‌های زیر استفاده کنید"
        )

# ===================== RUN =====================
if __name__ == "__main__":
    print("🤖 ربات در حال اجرا است...")
    print(f"📊 تعداد کاربران: {len(users)}")
    print(f"🛒 تعداد سبدهای فعال: {len(carts)}")
    executor.start_polling(dp, skip_updates=True)
