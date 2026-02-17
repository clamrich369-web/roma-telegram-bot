from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import *
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import logging
import json
import os
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)

TOKEN = "8543932711:AAFBzavfn2MunYAvnCKWiAEisUIyEmT04XQ"
ADMIN_IDS = [289763127]  # آیدی ادمین‌ها

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ===================== DATA FILES =====================
USERS_FILE = "users.json"
CARTS_FILE = "carts.json"
ORDERS_FILE = "orders.json"
MENU_FILE = "menu.json"
SETTINGS_FILE = "settings.json"

# ===================== LOAD/SAVE FUNCTIONS =====================
def load_data():
    global users, carts, orders, MENU, settings
    
    # بارگذاری منو
    if os.path.exists(MENU_FILE):
        with open(MENU_FILE, 'r', encoding='utf-8') as f:
            MENU = json.load(f)
    else:
        MENU = {
            "آلفردو": 450,
            "بولونز": 450,
            "پیتزا مرغ": 580,
            "پیتزا پپرونی": 580,
            "لازانیا": 580,
            "نوشابه": 50
        }
        save_menu()
    
    # بارگذاری تنظیمات
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
    else:
        settings = {
            "card_number": "6219-8618-1166-9158",
            "card_owner": "امین آقازاده",
            "phone": "09141604866",
            "address": "تهران، ...",
            "working_hours": "12 ظهر تا 12 شب",
            "instagram": "@roma.italianfoods"
        }
        save_settings()
    
    # بارگذاری کاربران
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users = json.load(f)
            # تبدیل کلیدها به اینتجر و اطمینان از یکسان بودن فرمت
            users = {int(k): v for k, v in users.items()}
    else:
        users = {}
    
    # بارگذاری سبد خرید
    if os.path.exists(CARTS_FILE):
        with open(CARTS_FILE, 'r', encoding='utf-8') as f:
            carts = json.load(f)
            carts = {int(k): v for k, v in carts.items()}
    else:
        carts = {}
    
    # بارگذاری سفارشات
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

def save_menu():
    with open(MENU_FILE, 'w', encoding='utf-8') as f:
        json.dump(MENU, f, ensure_ascii=False, indent=2)

def save_settings():
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

load_data()

# ===================== CONSTANTS =====================
CARD_NUMBER = settings["card_number"]
CARD_OWNER = settings["card_owner"]

# ===================== STATES =====================
class RegisterState(StatesGroup):
    waiting_for_contact = State()

class PaymentState(StatesGroup):
    waiting_for_receipt = State()

class OrderState(StatesGroup):
    waiting_for_quantity = State()

# ===================== ADMIN STATES =====================
class AdminState(StatesGroup):
    # منو
    waiting_for_food_name = State()
    waiting_for_food_price = State()
    waiting_for_edit_food = State()
    waiting_for_edit_price = State()
    waiting_for_delete_food = State()
    
    # تنظیمات
    waiting_for_card_number = State()
    waiting_for_card_owner = State()
    waiting_for_phone = State()
    waiting_for_address = State()
    waiting_for_working_hours = State()
    waiting_for_instagram = State()
    
    # گزارشات
    waiting_for_report_date = State()

# ===================== START =====================
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    uid = message.from_user.id
    
    # اگر ادمین است
    if uid in ADMIN_IDS:
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("👤 پنل مدیریت", "🍽 منوی غذا", "📊 وضعیت سفارش")
        await message.answer("👋 خوش آمدید مدیر!", reply_markup=kb)
        return
    
    # بررسی وجود کاربر در دیتابیس
    # توجه: uid را به اینتجر تبدیل می‌کنیم و با کلیدهای دیکشنری مقایسه می‌کنیم
    if uid in users:
        # کاربر قبلاً ثبت‌نام کرده است
        if uid not in carts:
            carts[uid] = {}
            save_carts()
            
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🍽 منوی غذا", "📞 تماس با ما", "📷 اینستاگرام", "📊 وضعیت سفارش")
        await message.answer("🍝 به رستوران ROMA خوش آمدید", reply_markup=kb)
    else:
        # کاربر جدید است - باید ثبت‌نام کند
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        button = KeyboardButton("📱 ارسال شماره", request_contact=True)
        kb.add(button)
        await message.answer(
            "🍝 به رستوران ROMA خوش آمدید\n"
            "🔹 برای استفاده از ربات، لطفاً شماره تماس خود را ارسال کنید\n"
            "🔸 این کار فقط یک بار انجام می‌شود",
            reply_markup=kb
        )
        await RegisterState.waiting_for_contact.set()

# ===================== REGISTER =====================
@dp.message_handler(content_types=ContentType.CONTACT, state=RegisterState.waiting_for_contact)
async def register(message: types.Message, state: FSMContext):
    uid = message.from_user.id
    
    # اگر ادمین است نیازی به ثبت‌نام ندارد
    if uid in ADMIN_IDS:
        await state.finish()
        return
    
    # ذخیره اطلاعات کاربر
    users[uid] = {
        "user_id": uid,  # ذخیره user_id برای اطمینان
        "name": message.from_user.full_name,
        "username": message.from_user.username,
        "phone": message.contact.phone_number,
        "register_date": str(datetime.now()),
        "total_orders": 0,
        "total_spent": 0,
        "first_seen": str(datetime.now()),
        "last_seen": str(datetime.now())
    }
    
    # ایجاد سبد خرید
    carts[uid] = {}
    
    # ذخیره در فایل
    save_users()
    save_carts()
    
    await state.finish()

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🍽 منوی غذا", "📞 تماس با ما", "📷 اینستاگرام", "📊 وضعیت سفارش")
    await message.answer(
        "✅ ثبت‌نام با موفقیت انجام شد!\n\n"
        "🍝 حالا می‌توانید از منوی غذا سفارش دهید",
        reply_markup=kb
    )

# ===================== CONTACT =====================
@dp.message_handler(lambda m: m.text == "📞 تماس با ما")
async def contact(message: types.Message):
    await message.answer(
        f"📞 {settings['phone']}\n"
        f"📍 آدرس: {settings['address']}\n"
        f"⏰ ساعت کاری: {settings['working_hours']}"
    )

@dp.message_handler(lambda m: m.text == "📷 اینستاگرام")
async def insta(message: types.Message):
    await message.answer(
        f"📷 اینستاگرام ما:\n"
        f"{settings['instagram']}"
    )

@dp.message_handler(lambda m: m.text == "📊 وضعیت سفارش")
async def check_order_status(message: types.Message):
    uid = message.from_user.id
    
    # به‌روزرسانی آخرین بازدید کاربر
    if uid in users:
        users[uid]['last_seen'] = str(datetime.now())
        save_users()
    
    if uid in orders:
        status_text = {
            "pending": "⏳ در انتظار انتخاب روش پرداخت",
            "waiting_for_payment": "💰 در انتظار پرداخت",
            "payment_received": "📸 فیش ارسال شده - در انتظار تأیید",
            "paid": "✅ پرداخت تأیید شده",
            "approved": "✅ سفارش تأیید شده",
            "preparing": "🍝 در حال آماده‌سازی",
            "ready": "✅ آماده تحویل",
            "delivered": "✅ تحویل داده شد",
            "rejected": "❌ رد شده",
            "payment_rejected": "❌ پرداخت رد شد"
        }
        
        status = orders[uid].get("status", "pending")
        text = status_text.get(status, "وضعیت نامشخص")
        
        order_items = "\n".join([f"• {k} × {v}" for k, v in orders[uid]['items'].items()])
        
        # تاریخ میلادی
        order_date = datetime.fromisoformat(orders[uid]['date']).strftime("%Y-%m-%d %H:%M")
        
        await message.answer(
            f"📊 وضعیت سفارش شما: {text}\n"
            f"📅 تاریخ: {order_date}\n\n"
            f"📝 سفارش:\n{order_items}\n"
            f"💰 مبلغ: {orders[uid]['total']} تومان"
        )
    else:
        await message.answer("❌ شما سفارش فعالی ندارید")

# ===================== ADMIN PANEL =====================
@dp.message_handler(lambda m: m.text == "👤 پنل مدیریت")
async def admin_panel(message: types.Message):
    uid = message.from_user.id
    
    if uid not in ADMIN_IDS:
        await message.answer("❌ شما دسترسی به این بخش ندارید!")
        return
    
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📋 مدیریت منو", callback_data="admin_menu"),
        InlineKeyboardButton("💰 مدیریت سفارشات", callback_data="admin_orders"),
        InlineKeyboardButton("📊 گزارش فروش", callback_data="admin_reports"),
        InlineKeyboardButton("👥 آمار کاربران", callback_data="admin_users"),
        InlineKeyboardButton("⚙️ تنظیمات", callback_data="admin_settings"),
        InlineKeyboardButton("📝 سفارشات در انتظار", callback_data="admin_pending")
    )
    
    await message.answer("🔰 پنل مدیریت", reply_markup=kb)

# ===================== ADMIN MENU MANAGEMENT =====================
@dp.callback_query_handler(lambda c: c.data == "admin_menu")
async def admin_menu(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("❌ دسترسی غیرمجاز")
        return
    
    text = "📋 مدیریت منو\n\n"
    text += "🍽 منوی فعلی:\n"
    for food, price in MENU.items():
        text += f"• {food}: {price} تومان\n"
    
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("➕ اضافه کردن غذا", callback_data="admin_add_food"),
        InlineKeyboardButton("✏️ ویرایش قیمت", callback_data="admin_edit_price"),
        InlineKeyboardButton("❌ حذف غذا", callback_data="admin_delete_food"),
        InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin")
    )
    
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "admin_add_food")
async def admin_add_food(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("🍽 نام غذای جدید را وارد کنید:")
    await AdminState.waiting_for_food_name.set()

@dp.message_handler(state=AdminState.waiting_for_food_name)
async def admin_get_food_name(message: types.Message, state: FSMContext):
    food_name = message.text.strip()
    await state.update_data(food_name=food_name)
    await message.answer(f"💰 قیمت {food_name} را وارد کنید (تومان):")
    await AdminState.waiting_for_food_price.set()

@dp.message_handler(state=AdminState.waiting_for_food_price)
async def admin_get_food_price(message: types.Message, state: FSMContext):
    try:
        price = int(message.text.strip())
        data = await state.get_data()
        food_name = data['food_name']
        
        MENU[food_name] = price
        save_menu()
        
        await state.finish()
        await message.answer(f"✅ غذای {food_name} با قیمت {price} تومان اضافه شد!")
        
        # برگشت به منوی مدیریت
        await admin_panel(message)
    except ValueError:
        await message.answer("❌ لطفاً یک عدد معتبر وارد کنید:")

@dp.callback_query_handler(lambda c: c.data == "admin_edit_price")
async def admin_edit_price(call: CallbackQuery, state: FSMContext):
    text = "✏️ ویرایش قیمت\n\n"
    text += "غذاهای موجود:\n"
    for i, (food, price) in enumerate(MENU.items(), 1):
        text += f"{i}. {food}: {price} تومان\n"
    
    kb = InlineKeyboardMarkup(row_width=1)
    for food in MENU.keys():
        kb.add(InlineKeyboardButton(food, callback_data=f"edit_food:{food}"))
    kb.add(InlineKeyboardButton("🔙 بازگشت", callback_data="admin_menu"))
    
    await call.message.edit_text(text + "\n\nغذا را انتخاب کنید:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("edit_food:"))
async def admin_select_food_to_edit(call: CallbackQuery, state: FSMContext):
    food = call.data.split(":")[1]
    await state.update_data(edit_food=food)
    await call.message.edit_text(f"💰 قیمت جدید برای {food} را وارد کنید (قیمت فعلی: {MENU[food]} تومان):")
    await AdminState.waiting_for_edit_price.set()

@dp.message_handler(state=AdminState.waiting_for_edit_price)
async def admin_update_price(message: types.Message, state: FSMContext):
    try:
        price = int(message.text.strip())
        data = await state.get_data()
        food = data['edit_food']
        
        old_price = MENU[food]
        MENU[food] = price
        save_menu()
        
        await state.finish()
        await message.answer(f"✅ قیمت {food} از {old_price} به {price} تومان تغییر یافت!")
        await admin_panel(message)
    except ValueError:
        await message.answer("❌ لطفاً یک عدد معتبر وارد کنید:")

@dp.callback_query_handler(lambda c: c.data == "admin_delete_food")
async def admin_delete_food(call: CallbackQuery, state: FSMContext):
    text = "❌ حذف غذا\n\n"
    text += "غذاهای موجود:\n"
    
    kb = InlineKeyboardMarkup(row_width=1)
    for food in MENU.keys():
        kb.add(InlineKeyboardButton(food, callback_data=f"delete_food:{food}"))
    kb.add(InlineKeyboardButton("🔙 بازگشت", callback_data="admin_menu"))
    
    await call.message.edit_text(text + "\n\nغذا را برای حذف انتخاب کنید:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("delete_food:"))
async def admin_confirm_delete(call: CallbackQuery):
    food = call.data.split(":")[1]
    
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ بله، حذف شود", callback_data=f"confirm_delete:{food}"),
        InlineKeyboardButton("❌ خیر، انصراف", callback_data="admin_menu")
    )
    
    await call.message.edit_text(f"⚠️ آیا از حذف {food} مطمئن هستید؟", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("confirm_delete:"))
async def admin_do_delete(call: CallbackQuery):
    food = call.data.split(":")[1]
    
    if food in MENU:
        del MENU[food]
        save_menu()
        await call.message.edit_text(f"✅ غذای {food} با موفقیت حذف شد!")
    
    await admin_panel(call.message)

# ===================== ADMIN ORDERS MANAGEMENT =====================
@dp.callback_query_handler(lambda c: c.data == "admin_orders")
async def admin_orders(call: CallbackQuery):
    text = "💰 مدیریت سفارشات\n\n"
    
    # سفارشات فعال
    active_orders = {uid: order for uid, order in orders.items() if order.get('status') not in ['delivered', 'rejected']}
    
    if not active_orders:
        text += "📭 سفارش فعالی وجود ندارد."
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin"))
        await call.message.edit_text(text, reply_markup=kb)
        return
    
    kb = InlineKeyboardMarkup(row_width=1)
    for uid, order in active_orders.items():
        status_emoji = {
            "pending": "⏳",
            "waiting_for_payment": "💰",
            "payment_received": "📸",
            "paid": "✅",
            "approved": "✅",
            "preparing": "🍝",
            "ready": "✅"
        }.get(order['status'], "📦")
        
        button_text = f"{status_emoji} سفارش {users[uid]['name']} - {order['total']} تومان"
        kb.add(InlineKeyboardButton(button_text, callback_data=f"view_order:{uid}"))
    
    kb.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin"))
    
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("view_order:"))
async def admin_view_order(call: CallbackQuery):
    uid = int(call.data.split(":")[1])
    
    if uid not in orders:
        await call.message.edit_text("❌ سفارش یافت نشد!")
        return
    
    order = orders[uid]
    user = users[uid]
    
    status_text = {
        "pending": "⏳ در انتظار پرداخت",
        "waiting_for_payment": "💰 در انتظار پرداخت",
        "payment_received": "📸 فیش ارسال شده",
        "paid": "✅ پرداخت شده",
        "approved": "✅ تأیید شده",
        "preparing": "🍝 در حال آماده‌سازی",
        "ready": "✅ آماده تحویل",
        "delivered": "✅ تحویل شده",
        "rejected": "❌ رد شده",
        "payment_rejected": "❌ پرداخت رد شد"
    }
    
    items_text = "\n".join([f"• {k} × {v}" for k, v in order['items'].items()])
    
    text = (
        f"📦 سفارش {user['name']}\n\n"
        f"👤 نام: {user['name']}\n"
        f"📞 شماره: {user['phone']}\n"
        f"🆔 آیدی: {uid}\n"
        f"💰 مبلغ: {order['total']} تومان\n"
        f"💳 روش: {order['method']}\n"
        f"📊 وضعیت: {status_text.get(order['status'], 'نامشخص')}\n\n"
        f"📝 آیتم‌ها:\n{items_text}"
    )
    
    kb = InlineKeyboardMarkup(row_width=2)
    
    # دکمه‌های بر اساس وضعیت
    if order['status'] == 'waiting_for_approval' or order['status'] == 'payment_received':
        kb.add(
            InlineKeyboardButton("✅ تأیید", callback_data=f"approve_order:{uid}"),
            InlineKeyboardButton("❌ رد", callback_data=f"reject_order:{uid}")
        )
    elif order['status'] == 'approved' or order['status'] == 'paid':
        kb.add(
            InlineKeyboardButton("✅ غذا آماده شد", callback_data=f"ready:{uid}"),
            InlineKeyboardButton("🏁 اتمام سفارش", callback_data=f"complete_order:{uid}")
        )
    elif order['status'] == 'ready':
        kb.add(InlineKeyboardButton("🏁 اتمام سفارش", callback_data=f"complete_order:{uid}"))
    
    kb.add(InlineKeyboardButton("🔙 بازگشت", callback_data="admin_orders"))
    
    await call.message.edit_text(text, reply_markup=kb)

# ===================== ADMIN REPORTS =====================
@dp.callback_query_handler(lambda c: c.data == "admin_reports")
async def admin_reports(call: CallbackQuery):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📊 گزارش روزانه", callback_data="report_daily"),
        InlineKeyboardButton("📈 گزارش هفتگی", callback_data="report_weekly"),
        InlineKeyboardButton("📅 گزارش ماهانه", callback_data="report_monthly"),
        InlineKeyboardButton("💰 گزارش فروش کل", callback_data="report_total"),
        InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin")
    )
    
    await call.message.edit_text("📊 گزارشات فروش", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "report_daily")
async def report_daily(call: CallbackQuery):
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    
    # فیلتر سفارشات امروز
    daily_orders = []
    total_sales = 0
    
    for uid, order in orders.items():
        if 'date' in order:
            order_date = datetime.fromisoformat(order['date']).date()
            if order_date == today and order.get('status') in ['delivered', 'paid', 'ready']:
                daily_orders.append(order)
                total_sales += order['total']
    
    text = (
        f"📊 گزارش فروش روزانه\n"
        f"📅 تاریخ: {today.strftime('%Y-%m-%d')}\n\n"
        f"💰 مجموع فروش: {total_sales} تومان\n"
        f"📦 تعداد سفارشات: {len(daily_orders)}\n\n"
    )
    
    if daily_orders:
        text += "📝 لیست سفارشات:\n"
        for i, order in enumerate(daily_orders, 1):
            text += f"{i}. {order['total']} تومان - {order.get('method', 'نامشخص')}\n"
    
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 بازگشت", callback_data="admin_reports"))
    
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "report_weekly")
async def report_weekly(call: CallbackQuery):
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    
    weekly_orders = []
    total_sales = 0
    
    for uid, order in orders.items():
        if 'date' in order:
            order_date = datetime.fromisoformat(order['date']).date()
            if week_ago <= order_date <= today and order.get('status') in ['delivered', 'paid', 'ready']:
                weekly_orders.append(order)
                total_sales += order['total']
    
    # فروش روزانه
    daily_sales = {}
    for order in weekly_orders:
        order_date = datetime.fromisoformat(order['date']).date()
        daily_sales[str(order_date)] = daily_sales.get(str(order_date), 0) + order['total']
    
    text = (
        f"📊 گزارش فروش هفتگی\n"
        f"📅 از {week_ago.strftime('%Y-%m-%d')}\n"
        f"📅 تا {today.strftime('%Y-%m-%d')}\n\n"
        f"💰 مجموع فروش: {total_sales} تومان\n"
        f"📦 تعداد سفارشات: {len(weekly_orders)}\n\n"
        f"📈 فروش روزانه:\n"
    )
    
    for date, amount in daily_sales.items():
        text += f"• {date}: {amount} تومان\n"
    
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 بازگشت", callback_data="admin_reports"))
    
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "report_monthly")
async def report_monthly(call: CallbackQuery):
    today = datetime.now()
    month_ago = today - timedelta(days=30)
    
    monthly_orders = []
    total_sales = 0
    
    for uid, order in orders.items():
        if 'date' in order:
            order_date = datetime.fromisoformat(order['date'])
            if month_ago <= order_date <= today and order.get('status') in ['delivered', 'paid', 'ready']:
                monthly_orders.append(order)
                total_sales += order['total']
    
    text = (
        f"📊 گزارش فروش ماهانه\n"
        f"📅 30 روز اخیر\n\n"
        f"💰 مجموع فروش: {total_sales} تومان\n"
        f"📦 تعداد سفارشات: {len(monthly_orders)}\n"
        f"📊 میانگین روزانه: {total_sales // 30 if total_sales else 0} تومان\n"
    )
    
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 بازگشت", callback_data="admin_reports"))
    
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "report_total")
async def report_total(call: CallbackQuery):
    total_sales = 0
    total_orders = 0
    completed_orders = 0
    
    for uid, order in orders.items():
        total_orders += 1
        if order.get('status') in ['delivered', 'paid', 'ready']:
            total_sales += order['total']
            completed_orders += 1
    
    text = (
        f"💰 گزارش فروش کل\n\n"
        f"📦 کل سفارشات: {total_orders}\n"
        f"✅ سفارشات تکمیل شده: {completed_orders}\n"
        f"❌ سفارشات لغو شده: {total_orders - completed_orders}\n"
        f"💰 مجموع فروش: {total_sales} تومان\n"
    )
    
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 بازگشت", callback_data="admin_reports"))
    
    await call.message.edit_text(text, reply_markup=kb)

# ===================== ADMIN USERS STATS =====================
@dp.callback_query_handler(lambda c: c.data == "admin_users")
async def admin_users(call: CallbackQuery):
    total_users = len(users)
    
    # کاربران فعال (کسانی که سفارش داشتن)
    active_users = set()
    for uid, order in orders.items():
        if order.get('status') in ['delivered', 'paid', 'ready']:
            active_users.add(uid)
    
    # کاربران جدید امروز
    today = datetime.now().date()
    new_users_today = 0
    for uid, user in users.items():
        if 'register_date' in user:
            register_date = datetime.fromisoformat(user['register_date']).date()
            if register_date == today:
                new_users_today += 1
    
    # کاربران آنلاین (آخرین بازدید در 24 ساعت اخیر)
    online_users = 0
    one_day_ago = datetime.now() - timedelta(days=1)
    for uid, user in users.items():
        if 'last_seen' in user:
            last_seen = datetime.fromisoformat(user['last_seen'])
            if last_seen > one_day_ago:
                online_users += 1
    
    # مجموع سفارشات کاربران
    total_orders = len([o for o in orders.values() if o.get('status') in ['delivered', 'paid', 'ready']])
    
    text = (
        f"👥 آمار کاربران\n\n"
        f"📊 کل کاربران: {total_users}\n"
        f"🆕 کاربران جدید امروز: {new_users_today}\n"
        f"🟢 کاربران آنلاین (24 ساعت): {online_users}\n"
        f"🛒 کاربران فعال: {len(active_users)}\n"
        f"📦 مجموع سفارشات: {total_orders}\n"
        f"💰 میانگین سفارش به ازای کاربر: {total_orders / total_users if total_users else 0:.1f}\n\n"
    )
    
    # 10 کاربر برتر
    user_orders = {}
    for uid, order in orders.items():
        if order.get('status') in ['delivered', 'paid', 'ready']:
            user_orders[uid] = user_orders.get(uid, 0) + 1
    
    top_users = sorted(user_orders.items(), key=lambda x: x[1], reverse=True)[:10]
    
    if top_users:
        text += "🏆 کاربران برتر:\n"
        for i, (uid, count) in enumerate(top_users, 1):
            user = users.get(uid, {})
            name = user.get('name', 'نامشخص')
            text += f"{i}. {name}: {count} سفارش\n"
    
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin"))
    
    await call.message.edit_text(text, reply_markup=kb)

# ===================== ADMIN SETTINGS =====================
@dp.callback_query_handler(lambda c: c.data == "admin_settings")
async def admin_settings(call: CallbackQuery):
    text = (
        f"⚙️ تنظیمات رستوران\n\n"
        f"💳 شماره کارت: {settings['card_number']}\n"
        f"👤 صاحب کارت: {settings['card_owner']}\n"
        f"📞 تلفن: {settings['phone']}\n"
        f"📍 آدرس: {settings['address']}\n"
        f"⏰ ساعت کاری: {settings['working_hours']}\n"
        f"📷 اینستاگرام: {settings['instagram']}\n"
    )
    
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("💳 ویرایش شماره کارت", callback_data="edit_card_number"),
        InlineKeyboardButton("👤 ویرایش صاحب کارت", callback_data="edit_card_owner"),
        InlineKeyboardButton("📞 ویرایش تلفن", callback_data="edit_phone"),
        InlineKeyboardButton("📍 ویرایش آدرس", callback_data="edit_address"),
        InlineKeyboardButton("⏰ ویرایش ساعت کاری", callback_data="edit_hours"),
        InlineKeyboardButton("📷 ویرایش اینستاگرام", callback_data="edit_instagram"),
        InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin")
    )
    
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "edit_card_number")
async def edit_card_number(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("💳 شماره کارت جدید را وارد کنید:")
    await AdminState.waiting_for_card_number.set()

@dp.message_handler(state=AdminState.waiting_for_card_number)
async def update_card_number(message: types.Message, state: FSMContext):
    settings['card_number'] = message.text.strip()
    save_settings()
    await state.finish()
    await message.answer("✅ شماره کارت با موفقیت به‌روزرسانی شد!")
    await admin_panel(message)

@dp.callback_query_handler(lambda c: c.data == "edit_card_owner")
async def edit_card_owner(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("👤 نام صاحب کارت جدید را وارد کنید:")
    await AdminState.waiting_for_card_owner.set()

@dp.message_handler(state=AdminState.waiting_for_card_owner)
async def update_card_owner(message: types.Message, state: FSMContext):
    settings['card_owner'] = message.text.strip()
    save_settings()
    await state.finish()
    await message.answer("✅ نام صاحب کارت با موفقیت به‌روزرسانی شد!")
    await admin_panel(message)

@dp.callback_query_handler(lambda c: c.data == "edit_phone")
async def edit_phone(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("📞 شماره تلفن جدید را وارد کنید:")
    await AdminState.waiting_for_phone.set()

@dp.message_handler(state=AdminState.waiting_for_phone)
async def update_phone(message: types.Message, state: FSMContext):
    settings['phone'] = message.text.strip()
    save_settings()
    await state.finish()
    await message.answer("✅ شماره تلفن با موفقیت به‌روزرسانی شد!")
    await admin_panel(message)

@dp.callback_query_handler(lambda c: c.data == "edit_address")
async def edit_address(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("📍 آدرس جدید را وارد کنید:")
    await AdminState.waiting_for_address.set()

@dp.message_handler(state=AdminState.waiting_for_address)
async def update_address(message: types.Message, state: FSMContext):
    settings['address'] = message.text.strip()
    save_settings()
    await state.finish()
    await message.answer("✅ آدرس با موفقیت به‌روزرسانی شد!")
    await admin_panel(message)

@dp.callback_query_handler(lambda c: c.data == "edit_hours")
async def edit_hours(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("⏰ ساعت کاری جدید را وارد کنید (مثال: 12 ظهر تا 12 شب):")
    await AdminState.waiting_for_working_hours.set()

@dp.message_handler(state=AdminState.waiting_for_working_hours)
async def update_hours(message: types.Message, state: FSMContext):
    settings['working_hours'] = message.text.strip()
    save_settings()
    await state.finish()
    await message.answer("✅ ساعت کاری با موفقیت به‌روزرسانی شد!")
    await admin_panel(message)

@dp.callback_query_handler(lambda c: c.data == "edit_instagram")
async def edit_instagram(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("📷 آدرس اینستاگرام جدید را وارد کنید:")
    await AdminState.waiting_for_instagram.set()

@dp.message_handler(state=AdminState.waiting_for_instagram)
async def update_instagram(message: types.Message, state: FSMContext):
    settings['instagram'] = message.text.strip()
    save_settings()
    await state.finish()
    await message.answer("✅ آدرس اینستاگرام با موفقیت به‌روزرسانی شد!")
    await admin_panel(message)

# ===================== ADMIN PENDING ORDERS =====================
@dp.callback_query_handler(lambda c: c.data == "admin_pending")
async def admin_pending(call: CallbackQuery):
    pending_orders = {uid: order for uid, order in orders.items() 
                     if order.get('status') in ['waiting_for_approval', 'payment_received']}
    
    if not pending_orders:
        text = "📭 سفارش در انتظاری وجود ندارد."
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin"))
        await call.message.edit_text(text, reply_markup=kb)
        return
    
    text = f"⏳ سفارشات در انتظار ({len(pending_orders)})\n\n"
    
    kb = InlineKeyboardMarkup(row_width=1)
    for uid, order in pending_orders.items():
        button_text = f"{users[uid]['name']} - {order['total']} تومان"
        kb.add(InlineKeyboardButton(button_text, callback_data=f"view_order:{uid}"))
    
    kb.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin"))
    
    await call.message.edit_text(text, reply_markup=kb)

# ===================== BACK TO ADMIN =====================
@dp.callback_query_handler(lambda c: c.data == "back_to_admin")
async def back_to_admin(call: CallbackQuery):
    await admin_panel(call.message)

# ===================== FOOD MENU =====================
@dp.message_handler(lambda m: m.text == "🍽 منوی غذا")
async def food_menu(message: types.Message):
    uid = message.from_user.id
    
    # اگر ادمین است
    if uid in ADMIN_IDS:
        await admin_panel(message)
        return
    
    # اگر کاربر عادی است - بررسی وجود در دیتابیس
    if uid not in users:
        await start(message)
        return
    
    # به‌روزرسانی آخرین بازدید
    if uid in users:
        users[uid]['last_seen'] = str(datetime.now())
        save_users()
    
    if uid not in carts:
        carts[uid] = {}
        save_carts()
    
    text = "🍽 منوی غذا:\n\n"
    for food, price in MENU.items():
        text += f"• {food}: {price} تومان\n"
    
    kb = InlineKeyboardMarkup(row_width=1)
    
    for food, price in MENU.items():
        button_text = f"🍽 {food} - {price} تومان"
        kb.add(InlineKeyboardButton(button_text, callback_data=f"select_food:{food}"))
    
    if carts[uid]:
        total_items = sum(carts[uid].values())
        total_price = sum(MENU[f] * q for f, q in carts[uid].items())
        kb.add(InlineKeyboardButton(f"🛒 مشاهده سبد خرید ({total_items} آیتم - {total_price} تومان)", callback_data="cart"))
    else:
        kb.add(InlineKeyboardButton("🛒 مشاهده سبد خرید (خالی)", callback_data="cart"))
    
    await message.answer(text, reply_markup=kb)

# ===================== SELECT FOOD =====================
@dp.callback_query_handler(lambda c: c.data.startswith("select_food:"))
async def select_food(call: CallbackQuery, state: FSMContext):
    # اگر ادمین است اجازه سفارش نده
    if call.from_user.id in ADMIN_IDS:
        await call.answer("⚠️ مدیران نمی‌توانند سفارش دهند!", show_alert=True)
        return
    
    food = call.data.split(":")[1]
    
    await state.update_data(selected_food=food)
    await OrderState.waiting_for_quantity.set()
    
    kb = InlineKeyboardMarkup(row_width=3)
    
    buttons = []
    for i in range(1, 6):
        buttons.append(InlineKeyboardButton(str(i), callback_data=f"qty:{i}"))
    kb.add(*buttons)
    
    kb.add(
        InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")
    )
    
    await call.message.edit_text(
        f"🍽 {food}\n"
        f"💰 قیمت واحد: {MENU[food]} تومان\n\n"
        f"🔢 تعداد مورد نظر را انتخاب کنید:",
        reply_markup=kb
    )

# ===================== ADD TO CART =====================
@dp.callback_query_handler(lambda c: c.data.startswith("qty:"), state=OrderState.waiting_for_quantity)
async def add_to_cart_with_qty(call: CallbackQuery, state: FSMContext):
    # اگر ادمین است اجازه نده
    if call.from_user.id in ADMIN_IDS:
        await state.finish()
        await call.answer("⚠️ مدیران نمی‌توانند سفارش دهند!", show_alert=True)
        return
    
    qty = int(call.data.split(":")[1])
    data = await state.get_data()
    food = data.get('selected_food')
    uid = call.from_user.id
    
    if not food:
        await call.message.edit_text("❌ خطا در انتخاب غذا!")
        await state.finish()
        return
    
    if uid not in carts:
        carts[uid] = {}
    
    if food not in carts[uid]:
        carts[uid][food] = 0
    carts[uid][food] += qty
    
    save_carts()
    await state.finish()
    
    total_items = sum(carts[uid].values())
    total_price = sum(MENU[f] * q for f, q in carts[uid].items())
    
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("➕ ادامه خرید", callback_data="back_to_menu"),
        InlineKeyboardButton("🛒 مشاهده سبد خرید", callback_data="cart"),
        InlineKeyboardButton("📦 تغییر تعداد", callback_data=f"change_qty:{food}")
    )
    
    await call.message.edit_text(
        f"✅ {food} با تعداد {qty} عدد به سبد خرید اضافه شد!\n\n"
        f"🛒 وضعیت سبد خرید:\n"
        f"📦 تعداد آیتم‌ها: {total_items}\n"
        f"💰 جمع کل: {total_price} تومان",
        reply_markup=kb
    )

# ===================== BACK TO MENU =====================
@dp.callback_query_handler(lambda c: c.data == "back_to_menu")
async def back_to_menu(call: CallbackQuery):
    uid = call.from_user.id
    
    text = "🍽 منوی غذا:\n\n"
    for food, price in MENU.items():
        text += f"• {food}: {price} تومان\n"
    
    kb = InlineKeyboardMarkup(row_width=1)
    
    for food, price in MENU.items():
        button_text = f"🍽 {food} - {price} تومان"
        kb.add(InlineKeyboardButton(button_text, callback_data=f"select_food:{food}"))
    
    if uid in carts and carts[uid]:
        total_items = sum(carts[uid].values())
        total_price = sum(MENU[f] * q for f, q in carts[uid].items())
        kb.add(InlineKeyboardButton(f"🛒 مشاهده سبد خرید ({total_items} آیتم - {total_price} تومان)", callback_data="cart"))
    else:
        kb.add(InlineKeyboardButton("🛒 مشاهده سبد خرید (خالی)", callback_data="cart"))
    
    await call.message.edit_text(text, reply_markup=kb)

# ===================== CHANGE QUANTITY =====================
@dp.callback_query_handler(lambda c: c.data.startswith("change_qty:"))
async def change_quantity(call: CallbackQuery):
    # اگر ادمین است اجازه نده
    if call.from_user.id in ADMIN_IDS:
        await call.answer("⚠️ مدیران نمی‌توانند سفارش دهند!", show_alert=True)
        return
    
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
    # اگر ادمین است اجازه نده
    if call.from_user.id in ADMIN_IDS:
        await call.answer("⚠️ مدیران نمی‌توانند سفارش دهند!", show_alert=True)
        return
    
    _, food, qty = call.data.split(":")
    uid = call.from_user.id
    
    if uid not in carts:
        carts[uid] = {}
    
    carts[uid][food] = int(qty)
    save_carts()
    
    await show_cart(call)

@dp.callback_query_handler(lambda c: c.data.startswith("increase_qty:"))
async def increase_quantity(call: CallbackQuery):
    # اگر ادمین است اجازه نده
    if call.from_user.id in ADMIN_IDS:
        await call.answer("⚠️ مدیران نمی‌توانند سفارش دهند!", show_alert=True)
        return
    
    food = call.data.split(":")[1]
    uid = call.from_user.id
    
    if uid not in carts:
        carts[uid] = {}
    
    carts[uid][food] = carts[uid].get(food, 1) + 1
    save_carts()
    
    await change_quantity(call)

@dp.callback_query_handler(lambda c: c.data.startswith("decrease_qty:"))
async def decrease_quantity(call: CallbackQuery):
    # اگر ادمین است اجازه نده
    if call.from_user.id in ADMIN_IDS:
        await call.answer("⚠️ مدیران نمی‌توانند سفارش دهند!", show_alert=True)
        return
    
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

# ===================== CART =====================
@dp.callback_query_handler(lambda c: c.data == "cart")
async def show_cart(call: CallbackQuery):
    uid = call.from_user.id
    
    # اگر ادمین است اجازه نده
    if uid in ADMIN_IDS:
        await call.answer("⚠️ مدیران نمی‌توانند سفارش دهند!", show_alert=True)
        return
    
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
    # اگر ادمین است اجازه نده
    if call.from_user.id in ADMIN_IDS:
        await call.answer("⚠️ مدیران نمی‌توانند سفارش دهند!", show_alert=True)
        return
    
    food = call.data.split(":")[1]
    uid = call.from_user.id
    
    if uid in carts and food in carts[uid]:
        del carts[uid][food]
        save_carts()
    
    await show_cart(call)

@dp.callback_query_handler(lambda c: c.data == "clear_cart")
async def clear_cart(call: CallbackQuery):
    # اگر ادمین است اجازه نده
    if call.from_user.id in ADMIN_IDS:
        await call.answer("⚠️ مدیران نمی‌توانند سفارش دهند!", show_alert=True)
        return
    
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
    
    # اگر ادمین است اجازه نده
    if uid in ADMIN_IDS:
        await call.answer("⚠️ مدیران نمی‌توانند سفارش دهند!", show_alert=True)
        return
    
    if uid not in carts or not carts[uid]:
        await call.message.edit_text("❌ سبد خرید شما خالی است!")
        return
    
    total = sum(MENU[f] * q for f, q in carts[uid].items())
    
    orders[uid] = {
        "items": carts[uid].copy(),
        "total": total,
        "method": None,
        "status": "pending",
        "date": str(datetime.now())
    }
    save_orders()
    
    # به‌روزرسانی آمار کاربر
    if uid in users:
        users[uid]['total_orders'] = users[uid].get('total_orders', 0) + 1
        users[uid]['total_spent'] = users[uid].get('total_spent', 0) + total
        save_users()
    
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
    
    # ارسال به ادمین‌ها
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
    
    await state.set_state(PaymentState.waiting_for_receipt)
    await state.update_data(order_uid=uid)
    
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("❌ انصراف", callback_data="cancel_payment"))
    
    await call.message.edit_text(
        f"💳 پرداخت کارت به کارت\n\n"
        f"🏦 اطلاعات کارت:\n"
        f"💳 شماره کارت: {settings['card_number']}\n"
        f"👤 به نام: {settings['card_owner']}\n\n"
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
    
    await state.set_state(PaymentState.waiting_for_receipt)
    await state.update_data(order_uid=uid)
    
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("❌ انصراف", callback_data="cancel_payment"))
    
    await call.message.edit_text(
        f"🚚 ارسال با پیک\n\n"
        f"برای ارسال سفارش با پیک:\n\n"
        f"1️⃣ مبلغ {orders[uid]['total']} تومان را به کارت زیر واریز کنید:\n"
        f"💳 {settings['card_number']}\n"
        f"👤 {settings['card_owner']}\n\n"
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
    
    # ارسال فیش به ادمین‌ها
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

# ===================== ADMIN APPROVALS =====================
@dp.callback_query_handler(lambda c: c.data.startswith("approve_order:"))
async def approve_order(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("❌ دسترسی غیرمجاز")
        return
    
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
    
    # اضافه کردن دکمه‌های بعدی
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ غذا آماده شد", callback_data=f"ready:{uid}"),
        InlineKeyboardButton("🏁 اتمام سفارش", callback_data=f"complete_order:{uid}")
    )
    
    # بررسی کنید که آیا متن وجود دارد یا خیر
    current_text = call.message.text or call.message.caption or ""
    await call.message.edit_text(
        current_text + "\n\n✅ سفارش تأیید شد",
        reply_markup=kb
    )
    await call.answer("✅ سفارش تأیید شد")

@dp.callback_query_handler(lambda c: c.data.startswith("reject_order:"))
async def reject_order(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("❌ دسترسی غیرمجاز")
        return
    
    uid = int(call.data.split(":")[1])
    
    if uid in orders:
        orders[uid]["status"] = "rejected"
        save_orders()
    
    await bot.send_message(
        uid,
        f"❌ متأسفانه سفارش شما رد شد!\n"
        f"لطفاً با پشتیبانی تماس بگیرید: {settings['phone']}"
    )
    
    # بررسی کنید که آیا متن وجود دارد یا خیر
    current_text = call.message.text or call.message.caption or ""
    await call.message.edit_text(
        current_text + "\n\n❌ سفارش رد شد"
    )
    await call.answer("❌ سفارش رد شد")

@dp.callback_query_handler(lambda c: c.data.startswith("approve_payment:"))
async def approve_payment(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("❌ دسترسی غیرمجاز")
        return
    
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
    
    # اضافه کردن دکمه‌های بعدی
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ غذا آماده شد", callback_data=f"ready:{uid}"),
        InlineKeyboardButton("🏁 اتمام سفارش", callback_data=f"complete_order:{uid}")
    )
    
    # برای پیام‌های عکس از caption استفاده می‌کنیم
    current_caption = call.message.caption or ""
    await call.message.edit_caption(
        current_caption + "\n\n✅ پرداخت تأیید شد",
        reply_markup=kb
    )
    await call.answer("✅ پرداخت تأیید شد")

@dp.callback_query_handler(lambda c: c.data.startswith("reject_payment:"))
async def reject_payment(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("❌ دسترسی غیرمجاز")
        return
    
    uid = int(call.data.split(":")[1])
    
    if uid in orders:
        orders[uid]["status"] = "payment_rejected"
        save_orders()
    
    await bot.send_message(
        uid,
        f"❌ پرداخت شما رد شد!\n\n"
        f"💳 لطفاً مجدداً تلاش کنید:\n"
        f"{settings['card_number']}\n"
        f"{settings['card_owner']}\n\n"
        f"یا با پشتیبانی تماس بگیرید: {settings['phone']}"
    )
    
    # برای پیام‌های عکس از caption استفاده می‌کنیم
    current_caption = call.message.caption or ""
    await call.message.edit_caption(
        current_caption + "\n\n❌ پرداخت رد شد"
    )
    await call.answer("❌ پرداخت رد شد")

@dp.callback_query_handler(lambda c: c.data.startswith("ready:"))
async def order_ready(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("❌ دسترسی غیرمجاز")
        return
    
    uid = int(call.data.split(":")[1])
    
    if uid in orders:
        orders[uid]["status"] = "ready"
        save_orders()
        
        # بررسی روش پرداخت و ارسال پیام مناسب
        if orders[uid].get("method") == "delivery":
            # اگر روش ارسال با پیک است
            await bot.send_message(
                uid,
                "✅ غذا به پیک تحویل داده شد!\n\n"
                "📞 همکاران ما به زودی با شما تماس می‌گیرند\n"
                "📍 لطفاً منتظر تماس پیک باشید"
            )
        else:
            # اگر روش‌های دیگر (حضوری یا کارت به کارت)
            await bot.send_message(
                uid,
                "✅ سفارش شما آماده است!\n\n"
                "🍝 می‌توانید برای تحویل سفارش خود مراجعه کنید"
            )
    
    # اضافه کردن دکمه اتمام سفارش
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🏁 اتمام سفارش", callback_data=f"complete_order:{uid}"))
    
    # بررسی کنید که آیا متن وجود دارد یا خیر
    current_text = call.message.text or call.message.caption or ""
    await call.message.edit_text(
        current_text + "\n\n✅ غذا آماده شد",
        reply_markup=kb
    )
    await call.answer("✅ اطلاع‌رسانی شد")

@dp.callback_query_handler(lambda c: c.data.startswith("complete_order:"))
async def complete_order(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("❌ دسترسی غیرمجاز")
        return
    
    uid = int(call.data.split(":")[1])
    
    if uid in orders:
        orders[uid]["status"] = "delivered"
        save_orders()
        
        if uid in carts:
            carts[uid] = {}
            save_carts()
        
        # بررسی روش پرداخت برای پیام نهایی
        if orders[uid].get("method") == "delivery":
            await bot.send_message(
                uid,
                "✅ سفارش شما با موفقیت تحویل داده شد!\n\n"
                "🍝 از انتخاب رستوران ROMA سپاسگزاریم\n"
                "🌟 منتظر حضور دوباره شما هستیم\n\n"
                "📞 اگر مشکلی بود با پشتیبانی تماس بگیرید"
            )
        else:
            await bot.send_message(
                uid,
                "✅ سفارش شما با موفقیت تحویل داده شد!\n\n"
                "🍝 از انتخاب رستوران ROMA سپاسگزاریم\n"
                "🌟 منتظر حضور دوباره شما هستیم"
            )
    
    # بررسی کنید که آیا متن وجود دارد یا خیر
    current_text = call.message.text or call.message.caption or ""
    await call.message.edit_text(
        current_text + "\n\n🏁 سفارش به پایان رسید"
    )
    await call.answer("✅ سفارش کامل شد")

# ===================== HELPERS =====================
@dp.message_handler(commands=["help"])
async def help_command(message: types.Message):
    uid = message.from_user.id
    
    if uid in ADMIN_IDS:
        await message.answer(
            "🤖 راهنمای مدیر:\n\n"
            "• /start - شروع مجدد\n"
            "• پنل مدیریت - دسترسی به پنل مدیریت\n"
            "• منوی غذا - مشاهده منو (برای مدیران قابل سفارش نیست)\n"
            "• وضعیت سفارش - بررسی وضعیت سفارش‌ها\n\n"
            "در پنل مدیریت می‌توانید:\n"
            "- منو را مدیریت کنید (افزودن/ویرایش/حذف)\n"
            "- سفارشات را مدیریت کنید\n"
            "- گزارش فروش بگیرید\n"
            "- آمار کاربران را ببینید\n"
            "- تنظیمات را تغییر دهید"
        )
    else:
        await message.answer(
            "🤖 راهنمای ربات:\n\n"
            "• /start - شروع مجدد\n"
            "• منوی غذا - مشاهده منو و سفارش\n"
            "• تماس با ما - اطلاعات تماس\n"
            "• اینستاگرام - صفحه اینستاگرام\n"
            "• وضعیت سفارش - بررسی وضعیت سفارش\n\n"
            f"برای هر سوال با پشتیبانی تماس بگیرید: {settings['phone']}"
        )

# ===================== FALLBACK =====================
@dp.message_handler()
async def fallback(message: types.Message):
    uid = message.from_user.id
    
    if uid in ADMIN_IDS:
        await message.answer(
            "❌ دستور نامعتبر!\n"
            "لطفاً از دکمه‌های زیر استفاده کنید"
        )
    elif uid not in users:
        await start(message)
    else:
        await message.answer(
            "❌ دستور نامعتبر!\n"
            "لطفاً از دکمه‌های زیر استفاده کنید"
        )

# ===================== RUN =====================
if __name__ == "__main__":
    print("🤖 ربات در حال اجرا است...")
    print(f"👤 تعداد کاربران: {len(users)}")
    print(f"🛒 تعداد سبدهای فعال: {len(carts)}")
    print(f"📦 تعداد سفارشات: {len(orders)}")
    print(f"👑 ادمین‌ها: {ADMIN_IDS}")
    executor.start_polling(dp, skip_updates=True)
