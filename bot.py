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
    
    # بارگذاری کاربران
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users = json.load(f)
            # تبدیل کلیدها به اینتجر
            users = {int(k): v for k, v in users.items()}
    else:
        users = {}
    
    # بارگذاری سبد خرید
    if os.path.exists(CARTS_FILE):
        with open(CARTS_FILE, 'r', encoding='utf-8') as f:
            carts = json.load(f)
            # تبدیل کلیدها به اینتجر
            carts = {int(k): v for k, v in carts.items()}
    else:
        carts = {}
    
    # بارگذاری سفارشات
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
            orders = json.load(f)
            # تبدیل کلیدها به اینتجر
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

# بارگذاری اطلاعات هنگام شروع
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

# ===================== START =====================
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    uid = message.from_user.id
    
    # بررسی وجود کاربر در فایل
    if str(uid) in users or uid in users:
        # اطمینان از وجود سبد خرید
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
    
    # ذخیره در فایل
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
    
    # بررسی ثبت‌نام کاربر
    if str(uid) not in users and uid not in users:
        await start(message)
        return
    
    # اطمینان از وجود سبد خرید
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
    
    # دکمه مشاهده سبد خرید
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
    
    # اضافه کردن مستقیم به سبد خرید
    if uid not in carts:
        carts[uid] = {}
    
    if food not in carts[uid]:
        carts[uid][food] = 0
    carts[uid][food] += 1
    
    # ذخیره سبد خرید
    save_carts()
    
    # محاسبه تعداد کل آیتم‌ها و قیمت کل
    total_items = sum(carts[uid].values())
    total_price = sum(MENU[f] * q for f, q in carts[uid].items())
    
    # ایجاد کیبورد برای ادامه خرید
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
    
    # دکمه‌های انتخاب تعداد
    buttons = []
    for i in range(1, 6):
        if i == current_qty:
            buttons.append(InlineKeyboardButton(f"✅ {i}", callback_data=f"set_qty:{food}:{i}"))
        else:
            buttons.append(InlineKeyboardButton(str(i), callback_data=f"set_qty:{food}:{i}"))
    kb.add(*buttons)
    
    # دکمه‌های کمکی
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
    
    # نمایش سبد خرید به‌روز شده
    await show_cart(call)

@dp.callback_query_handler(lambda c: c.data.startswith("increase_qty:"))
async def increase_quantity(call: CallbackQuery):
    food = call.data.split(":")[1]
    uid = call.from_user.id
    
    if uid not in carts:
        carts[uid] = {}
    
    carts[uid][food] = carts[uid].get(food, 1) + 1
    save_carts()
    
    # نمایش دوباره صفحه تغییر تعداد
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
        # اگر تعداد به 1 برسد و کاربر کاهش دهد، آیتم حذف می‌شود
        await delete_item(call)

# ===================== BACK TO MENU =====================
@dp.callback_query_handler(lambda c: c.data == "back_to_menu")
async def back_to_menu(call: CallbackQuery):
    # اینجا باید یک پیام جدید ارسال کنیم، چون در کالبک نمی‌توانیم از message_handler استفاده کنیم
    uid = call.from_user.id
    
    text = "🍽 منوی غذا:\n\n"
    for food, price in MENU.items():
        text += f"• {food}: {price} تومان\n"
    
    kb = InlineKeyboardMarkup(row_width=1)
    
    for food, price in MENU.items():
        button_text = f"➕ {food} - {price} تومان"
        kb.add(InlineKeyboardButton(button_text, callback_data=f"add_to_cart:{food}"))
    
    # دکمه مشاهده سبد خرید
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
    orders[uid]["method"] = "cash"
    save_orders()
    
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
    
    # پاک کردن سبد خرید بعد از ثبت سفارش
    carts[uid] = {}
    save_carts()

# بقیه کدهای پرداخت و ادمین به همین شکل ادامه پیدا می‌کند...

# ===================== RUN =====================
if __name__ == "__main__":
    print("🤖 ربات در حال اجرا است...")
    print(f"📊 تعداد کاربران: {len(users)}")
    print(f"🛒 تعداد سبدهای فعال: {len(carts)}")
    executor.start_polling(dp, skip_updates=True)
