# -*- coding: utf-8 -*-
# ============================================================
#   AMMAR DEVX 🦁 - Improved Bot with All Features
#   Features: User Mgmt, Bot Control, Analytics, Payment,
#             Notifications, Security
# ============================================================

import telebot
import subprocess
import os
import zipfile
import tempfile
import shutil
from telebot import types
import time
from datetime import datetime, timedelta
import psutil
import sqlite3
import json
import logging
import signal
import threading
import re
import sys
import atexit
import requests
import random
import hashlib
from collections import defaultdict
from functools import wraps

# --- Flask Keep Alive ---
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "🤖 AMMAR DEVX 🦁 is Running!"

@app.route('/health')
def health():
    return {"status": "healthy", "uptime": get_uptime()}

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    print("✅ Flask Keep-Alive server started.")

# --- Configuration (Use environment variables!) ---
TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_TOKEN_HERE')  # ⚠️ Set in environment!
OWNER_ID = int(os.environ.get('OWNER_ID', '7847937078'))
ADMIN_ID = int(os.environ.get('ADMIN_ID', '7847937078'))
YOUR_USERNAME = os.environ.get('YOUR_USERNAME', '@AmmarDevx')
UPDATE_CHANNEL = os.environ.get('UPDATE_CHANNEL', 'https://t.me/ammar_devs')

# Folder setup
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_BOTS_DIR = os.path.join(BASE_DIR, 'upload_bots')
IROTECH_DIR = os.path.join(BASE_DIR, 'inf')
DATABASE_PATH = os.path.join(IROTECH_DIR, 'bot_data.db')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# File upload limits
FREE_USER_LIMIT = 10
SUBSCRIBED_USER_LIMIT = 15
ADMIN_LIMIT = 999
OWNER_LIMIT = float('inf')

# ✅ NEW: Security limits
RATE_LIMIT_MESSAGES = 10       # max messages per window
RATE_LIMIT_WINDOW = 60         # seconds
MAX_WARNINGS = 3               # warnings before auto-ban
MAX_SCRIPT_RUNTIME = 3600      # 1 hour max per script
MAX_FILE_SIZE_MB = 20          # max upload size

# ✅ NEW: Subscription plans
SUBSCRIPTION_PLANS = {
    'basic':   {'days': 30,  'price': 100,  'limit': 15,  'label': '⭐ Basic'},
    'pro':     {'days': 30,  'price': 250,  'limit': 30,  'label': '💎 Pro'},
    'premium': {'days': 30,  'price': 500,  'limit': 999, 'label': '👑 Premium'},
}

# Create directories
os.makedirs(UPLOAD_BOTS_DIR, exist_ok=True)
os.makedirs(IROTECH_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Initialize bot
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# --- In-memory Data Structures ---
bot_scripts = {}
user_subscriptions = {}
user_files = {}
active_users = set()
admin_ids = {ADMIN_ID, OWNER_ID}
bot_locked = False
bot_start_time = datetime.now()
user_operations = {}

# ✅ NEW: Security tracking (thread-safe)
data_lock = threading.Lock()
rate_limit_data = defaultdict(list)      # user_id -> [timestamps]
user_warnings = defaultdict(int)         # user_id -> warning count
banned_users = set()                     # banned user ids
user_warn_reasons = defaultdict(list)    # user_id -> [reasons]

# ✅ NEW: Analytics tracking
analytics = {
    'commands_today': defaultdict(int),  # command -> count
    'uploads_today': 0,
    'scripts_run_today': 0,
    'errors_today': 0,
    'daily_active': set(),
    'last_reset': datetime.now().date(),
}

# ✅ NEW: Notification settings
notify_settings = {
    'crash_alerts': True,
    'new_user_alerts': True,
    'payment_alerts': True,
    'daily_report': True,
    'report_time': '08:00',
}

# ✅ NEW: Pending payments
pending_payments = {}   # user_id -> {plan, amount, ref_id, timestamp}
payment_history = []    # list of completed payments

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, 'bot.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================
# 🛡️ SECURITY: Rate Limiting & Ban System
# ============================================================

def is_rate_limited(user_id):
    """Check if user exceeded message rate limit"""
    if user_id in admin_ids or user_id == OWNER_ID:
        return False
    now = time.time()
    with data_lock:
        # Remove old timestamps outside window
        rate_limit_data[user_id] = [
            t for t in rate_limit_data[user_id]
            if now - t < RATE_LIMIT_WINDOW
        ]
        if len(rate_limit_data[user_id]) >= RATE_LIMIT_MESSAGES:
            return True
        rate_limit_data[user_id].append(now)
    return False

def is_banned(user_id):
    """Check if user is banned"""
    return user_id in banned_users

def security_check(func):
    """Decorator: checks ban + rate limit before any handler"""
    @wraps(func)
    def wrapper(message, *args, **kwargs):
        uid = message.from_user.id if hasattr(message, 'from_user') else None
        if uid is None:
            return func(message, *args, **kwargs)
        if is_banned(uid):
            try:
                bot.reply_to(message, "🚫 <b>You are banned.</b>\nContact owner to appeal.")
            except Exception:
                pass
            return
        if bot_locked and uid not in admin_ids and uid != OWNER_ID:
            bot.reply_to(message, "🔒 Bot is currently locked.")
            return
        if is_rate_limited(uid):
            try:
                bot.reply_to(message, "⚠️ <b>Slow down!</b> Too many requests. Wait a moment.")
            except Exception:
                pass
            return
        return func(message, *args, **kwargs)
    return wrapper

def ban_user(user_id, reason="No reason", banned_by=None):
    """Ban a user"""
    with data_lock:
        banned_users.add(user_id)
    save_ban_db(user_id, reason, banned_by)
    log_action(user_id, "BAN", f"Banned: {reason}")

def unban_user(user_id):
    """Unban a user"""
    with data_lock:
        banned_users.discard(user_id)
    remove_ban_db(user_id)
    log_action(user_id, "UNBAN", "Unbanned")

def warn_user(user_id, reason="Violation"):
    """Warn a user, auto-ban after MAX_WARNINGS"""
    with data_lock:
        user_warnings[user_id] += 1
        user_warn_reasons[user_id].append(reason)
        count = user_warnings[user_id]
    save_warning_db(user_id, reason)
    if count >= MAX_WARNINGS:
        ban_user(user_id, f"Auto-ban after {MAX_WARNINGS} warnings")
        return count, True  # warned, auto-banned
    return count, False


# ============================================================
# 📊 ANALYTICS: Track Usage
# ============================================================

def reset_daily_analytics():
    """Reset daily analytics at midnight"""
    today = datetime.now().date()
    if analytics['last_reset'] != today:
        analytics['commands_today'] = defaultdict(int)
        analytics['uploads_today'] = 0
        analytics['scripts_run_today'] = 0
        analytics['errors_today'] = 0
        analytics['daily_active'] = set()
        analytics['last_reset'] = today

def track_command(command, user_id):
    """Track command usage"""
    reset_daily_analytics()
    analytics['commands_today'][command] += 1
    analytics['daily_active'].add(user_id)

def track_upload():
    reset_daily_analytics()
    analytics['uploads_today'] += 1

def track_script_run():
    reset_daily_analytics()
    analytics['scripts_run_today'] += 1

def track_error():
    reset_daily_analytics()
    analytics['errors_today'] += 1

def get_analytics_report():
    """Generate analytics report text"""
    reset_daily_analytics()
    top_cmds = sorted(analytics['commands_today'].items(), key=lambda x: x[1], reverse=True)[:5]
    top_str = "\n".join([f"║  • /{cmd}: {cnt}" for cmd, cnt in top_cmds]) or "║  • None yet"
    running_bots = len([k for k in bot_scripts if is_bot_running_check(k)])
    active_subs = len([u for u, d in user_subscriptions.items() if d['expiry'] > datetime.now()])
    return f"""
╔══════════════════════════════════════╗
║     📊 <b>AMMAR DEVX ANALYTICS</b> 📊      ║
╠══════════════════════════════════════╣
║ 📅 <b>Today ({datetime.now().strftime('%d/%m/%Y')}):</b>
║  • Active Users: {len(analytics['daily_active'])}
║  • Uploads: {analytics['uploads_today']}
║  • Scripts Run: {analytics['scripts_run_today']}
║  • Errors: {analytics['errors_today']}
╠══════════════════════════════════════╣
║ 🏆 <b>Top Commands Today:</b>
{top_str}
╠══════════════════════════════════════╣
║ 📈 <b>Overall:</b>
║  • Total Users: {len(active_users)}
║  • Active Subs: {active_subs}
║  • Running Bots: {running_bots}
║  • Banned Users: {len(banned_users)}
║  • Uptime: {get_uptime()}
╚══════════════════════════════════════╝"""


# ============================================================
# 💰 PAYMENT / SUBSCRIPTION SYSTEM
# ============================================================

def generate_ref_id(user_id, plan):
    """Generate unique payment reference"""
    raw = f"{user_id}{plan}{time.time()}{random.randint(1000,9999)}"
    return "PAY-" + hashlib.md5(raw.encode()).hexdigest()[:10].upper()

def create_payment_request(user_id, plan):
    """Create a payment request for a plan"""
    if plan not in SUBSCRIPTION_PLANS:
        return None
    ref_id = generate_ref_id(user_id, plan)
    pending_payments[user_id] = {
        'plan': plan,
        'amount': SUBSCRIPTION_PLANS[plan]['price'],
        'ref_id': ref_id,
        'timestamp': datetime.now(),
        'label': SUBSCRIPTION_PLANS[plan]['label'],
    }
    return pending_payments[user_id]

def approve_payment(user_id, approved_by):
    """Admin approves a pending payment"""
    if user_id not in pending_payments:
        return False, "No pending payment found"
    payment = pending_payments.pop(user_id)
    plan = payment['plan']
    days = SUBSCRIPTION_PLANS[plan]['days']
    expiry = datetime.now() + timedelta(days=days)
    user_subscriptions[user_id] = {'expiry': expiry, 'plan': plan}
    save_subscription(user_id, expiry, plan)
    payment_history.append({
        'user_id': user_id,
        'plan': plan,
        'amount': payment['amount'],
        'ref_id': payment['ref_id'],
        'timestamp': datetime.now(),
        'approved_by': approved_by,
    })
    log_action(user_id, "PAYMENT_APPROVED", f"Plan: {plan}, Days: {days}")
    # Notify owner
    if notify_settings['payment_alerts']:
        try:
            bot.send_message(OWNER_ID,
                f"💰 <b>Payment Approved!</b>\n"
                f"👤 User: {user_id}\n"
                f"📦 Plan: {payment['label']}\n"
                f"💵 Amount: {payment['amount']} PKR\n"
                f"✅ By: {approved_by}")
        except Exception:
            pass
    return True, expiry

def reject_payment(user_id, reason="Rejected by admin"):
    """Admin rejects a payment"""
    if user_id not in pending_payments:
        return False
    pending_payments.pop(user_id)
    log_action(user_id, "PAYMENT_REJECTED", reason)
    return True

def get_subscription_keyboard():
    """Inline keyboard for subscription plans"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    for plan_key, plan in SUBSCRIPTION_PLANS.items():
        markup.add(types.InlineKeyboardButton(
            f"{plan['label']} — {plan['price']} PKR / {plan['days']} days ({plan['limit']} files)",
            callback_data=f"buy_{plan_key}"
        ))
    markup.add(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_payment"))
    return markup


# ============================================================
# 🔔 NOTIFICATIONS SYSTEM
# ============================================================

def notify_owner(message_text):
    """Send notification to owner"""
    try:
        bot.send_message(OWNER_ID, f"🔔 <b>NOTIFICATION</b>\n{message_text}")
    except Exception as e:
        logger.error(f"Notify owner failed: {e}")

def notify_crash(script_key, file_name, user_id, error_snippet=""):
    """Notify owner when a script crashes"""
    if not notify_settings['crash_alerts']:
        return
    try:
        bot.send_message(OWNER_ID,
            f"💥 <b>Script Crashed!</b>\n"
            f"📄 File: <code>{file_name}</code>\n"
            f"👤 User: {user_id}\n"
            f"🕐 Time: {datetime.now().strftime('%H:%M:%S')}\n"
            f"❗ Error: <code>{error_snippet[:200]}</code>")
        # Also notify the user
        bot.send_message(user_id,
            f"💥 <b>Your script crashed!</b>\n"
            f"📄 <code>{file_name}</code>\n"
            f"Use 📋 Logs to check what went wrong.")
    except Exception as e:
        logger.error(f"Crash notify failed: {e}")

def notify_new_user(user_id, username, first_name):
    """Notify owner when new user joins"""
    if not notify_settings['new_user_alerts']:
        return
    try:
        bot.send_message(OWNER_ID,
            f"👤 <b>New User Joined!</b>\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"👤 Name: {first_name}\n"
            f"📛 Username: @{username or 'N/A'}\n"
            f"👥 Total Users: {len(active_users)}")
    except Exception as e:
        logger.error(f"New user notify failed: {e}")

def send_daily_report():
    """Send daily analytics report to owner"""
    if not notify_settings['daily_report']:
        return
    report = get_analytics_report()
    try:
        bot.send_message(OWNER_ID, f"📊 <b>Daily Report</b>\n{report}")
    except Exception as e:
        logger.error(f"Daily report failed: {e}")

def start_daily_report_scheduler():
    """Background thread: send report at configured time daily"""
    def scheduler():
        while True:
            try:
                now = datetime.now().strftime('%H:%M')
                if now == notify_settings['report_time']:
                    send_daily_report()
                    time.sleep(61)  # avoid double-send
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
            time.sleep(30)
    t = Thread(target=scheduler, daemon=True)
    t.start()

def start_script_watchdog():
    """Background thread: watch for script runtime limit & crashes"""
    def watchdog():
        while True:
            try:
                now = datetime.now()
                for script_key in list(bot_scripts.keys()):
                    info = bot_scripts.get(script_key)
                    if not info:
                        continue
                    # Check runtime limit
                    runtime = (now - info.get('start_time', now)).total_seconds()
                    if runtime > MAX_SCRIPT_RUNTIME:
                        logger.warning(f"Script {script_key} exceeded runtime limit, killing.")
                        kill_process_tree(info)
                        cleanup_script(script_key)
                        try:
                            bot.send_message(info['user_id'],
                                f"⏱️ <b>Script auto-stopped!</b>\n"
                                f"📄 <code>{info['file_name']}</code>\n"
                                f"Reason: Exceeded {MAX_SCRIPT_RUNTIME//3600}h runtime limit.")
                        except Exception:
                            pass
                        continue
                    # Check if crashed unexpectedly
                    if info.get('process') and not is_bot_running_check(script_key):
                        log_path = info.get('log_path', '')
                        error_snippet = ""
                        if log_path and os.path.exists(log_path):
                            with open(log_path, 'r', errors='ignore') as f:
                                error_snippet = f.read()[-300:]
                        notify_crash(script_key, info['file_name'], info['user_id'], error_snippet)
                        cleanup_script(script_key)
            except Exception as e:
                logger.error(f"Watchdog error: {e}")
            time.sleep(15)
    t = Thread(target=watchdog, daemon=True)
    t.start()


# ============================================================
# 📊 ANIMATION CLASSES (unchanged)
# ============================================================

class ProgressAnimation:
    @staticmethod
    def create_progress_bar(current, total, length=4):
        progress = int((current / total) * length)
        bar = "🟩" * progress + "⬜" * (length - progress)
        return f"[{bar}]"

class TerminalAnimation:
    @staticmethod
    def create_terminal_box(title, content, status="running"):
        status_icons = {"running": "🟢", "stopped": "🔴", "error": "⚠️", "success": "✅", "loading": "⏳"}
        icon = status_icons.get(status, "📦")
        return f"\n╔═══════════════════════════════════╗\n║ {icon} {title[:30]:<30} ║\n╠═══════════════════════════════════╣\n║ {content[:32]:<32} ║\n╚═══════════════════════════════════╝\n"


# ============================================================
# 🎬 ANIMATED MESSAGE FUNCTIONS
# ============================================================

def send_animated_message(chat_id, final_text, animation_type="loading", duration=2, steps=4):
    action_map = {
        "loading": "Authenticating session", "upload": "Uploading file",
        "download": "Downloading file", "delete": "Deleting file",
        "run": "Starting script", "stop": "Stopping script",
        "install": "Installing dependencies", "terminal": "Initializing terminal"
    }
    action_text = action_map.get(animation_type, "Processing")
    msg = None
    try:
        for i in range(steps + 1):
            percent = int((i / steps) * 100)
            bar = "🟩" * i + "⬜" * (steps - i)
            display = f"⚙️ 𝐋ᴏᴀᴅɪɴɢ... ({percent}%)\n[{bar}] {action_text}..."
            if i == 0:
                msg = bot.send_message(chat_id, display)
            else:
                try:
                    bot.edit_message_text(display, chat_id, msg.message_id)
                except Exception:
                    pass
            time.sleep(duration / steps)
        try:
            bot.edit_message_text(final_text, chat_id, msg.message_id, parse_mode='HTML')
        except Exception:
            bot.send_message(chat_id, final_text, parse_mode='HTML')
        return msg
    except Exception as e:
        logger.error(f"Animation error: {e}")
        return bot.send_message(chat_id, final_text, parse_mode='HTML')

def send_spinner_animation(chat_id, text, duration=3):
    return send_animated_message(chat_id, text, animation_type="loading", duration=duration)


# ============================================================
# 🔧 UTILITY FUNCTIONS
# ============================================================

def get_uptime():
    uptime = datetime.now() - bot_start_time
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"

def format_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"

def get_system_stats():
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    return {
        'cpu': cpu,
        'memory_used': memory.percent,
        'memory_total': format_size(memory.total),
        'disk_used': disk.percent,
        'disk_total': format_size(disk.total),
        'uptime': get_uptime()
    }

def create_mini_bar(percentage, length=20):
    filled = int((percentage / 100) * length)
    bar = '█' * filled + '░' * (length - filled)
    return f"║ [{bar}]"

def create_system_stats_message():
    stats = get_system_stats()
    running_bots = len([k for k in bot_scripts if is_bot_running_check(k)])
    return f"""
╔══════════════════════════════════════╗
║       📊 <b>AMMAR DEVX STATS</b> 📊         ║
╠══════════════════════════════════════╣
║ 🖥️ <b>CPU:</b> {stats['cpu']}%
{create_mini_bar(stats['cpu'])}
║ 🧠 <b>Memory:</b> {stats['memory_used']}% / {stats['memory_total']}
{create_mini_bar(stats['memory_used'])}
║ 💾 <b>Disk:</b> {stats['disk_used']}% / {stats['disk_total']}
{create_mini_bar(stats['disk_used'])}
║ ⏱️ <b>Uptime:</b> {stats['uptime']}
║ 🤖 <b>Running Bots:</b> {running_bots}
║ 👥 <b>Total Users:</b> {len(active_users)}
║ 🚫 <b>Banned Users:</b> {len(banned_users)}
╚══════════════════════════════════════╝"""

def is_bot_running_check(script_key):
    script_info = bot_scripts.get(script_key)
    if script_info and script_info.get('process'):
        try:
            proc = psutil.Process(script_info['process'].pid)
            return proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
        except Exception:
            return False
    return False

def is_bot_running(script_owner_id, file_name):
    script_key = f"{script_owner_id}_{file_name}"
    script_info = bot_scripts.get(script_key)
    if script_info and script_info.get('process'):
        try:
            proc = psutil.Process(script_info['process'].pid)
            is_running = proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
            if not is_running:
                cleanup_script(script_key)
            return is_running
        except psutil.NoSuchProcess:
            cleanup_script(script_key)
            return False
        except Exception as e:
            logger.error(f"Error checking process: {e}")
            return False
    return False

def cleanup_script(script_key):
    if script_key in bot_scripts:
        script_info = bot_scripts[script_key]
        try:
            lf = script_info.get('log_file')
            if lf and hasattr(lf, 'close') and not lf.closed:
                lf.close()
        except Exception:
            pass
        del bot_scripts[script_key]
        logger.info(f"Cleaned up script: {script_key}")

def kill_process_tree(process_info):
    try:
        lf = process_info.get('log_file')
        if lf and hasattr(lf, 'close') and not lf.closed:
            lf.close()
    except Exception:
        pass
    process = process_info.get('process')
    if process and hasattr(process, 'pid'):
        try:
            parent = psutil.Process(process.pid)
            children = parent.children(recursive=True)
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            gone, alive = psutil.wait_procs(children, timeout=2)
            for p in alive:
                try:
                    p.kill()
                except Exception:
                    pass
            try:
                parent.terminate()
                parent.wait(timeout=2)
            except (psutil.TimeoutExpired, psutil.NoSuchProcess):
                try:
                    parent.kill()
                except Exception:
                    pass
        except psutil.NoSuchProcess:
            pass
        except Exception as e:
            logger.error(f"Kill error: {e}")


# ============================================================
# 🗄️ DATABASE FUNCTIONS (Improved: single connection helper)
# ============================================================

def get_db():
    """Get a database connection"""
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    logger.info(f"Initializing DB at: {DATABASE_PATH}")
    try:
        conn = get_db()
        c = conn.cursor()
        c.executescript('''
            CREATE TABLE IF NOT EXISTS subscriptions
                (user_id INTEGER PRIMARY KEY, expiry TEXT, plan TEXT DEFAULT 'basic');
            CREATE TABLE IF NOT EXISTS user_files
                (user_id INTEGER, file_name TEXT, file_type TEXT, upload_time TEXT,
                 file_size INTEGER, PRIMARY KEY (user_id, file_name));
            CREATE TABLE IF NOT EXISTS active_users
                (user_id INTEGER PRIMARY KEY, username TEXT, first_seen TEXT, last_seen TEXT);
            CREATE TABLE IF NOT EXISTS admins
                (user_id INTEGER PRIMARY KEY);
            CREATE TABLE IF NOT EXISTS bot_logs
                (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                 action TEXT, details TEXT, timestamp TEXT);
            CREATE TABLE IF NOT EXISTS running_scripts
                (script_key TEXT PRIMARY KEY, user_id INTEGER, file_name TEXT,
                 start_time TEXT, pid INTEGER);
            CREATE TABLE IF NOT EXISTS banned_users
                (user_id INTEGER PRIMARY KEY, reason TEXT, banned_by INTEGER, banned_at TEXT);
            CREATE TABLE IF NOT EXISTS user_warnings
                (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                 reason TEXT, warned_at TEXT);
            CREATE TABLE IF NOT EXISTS payment_history
                (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, plan TEXT,
                 amount INTEGER, ref_id TEXT, approved_by INTEGER, timestamp TEXT);
        ''')
        c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (OWNER_ID,))
        if ADMIN_ID != OWNER_ID:
            c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (ADMIN_ID,))
        conn.commit()
        conn.close()
        logger.info("DB initialized.")
    except Exception as e:
        logger.error(f"DB init error: {e}", exc_info=True)

def load_data():
    logger.info("Loading data from DB...")
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT user_id, expiry, plan FROM subscriptions')
        for row in c.fetchall():
            try:
                user_subscriptions[row['user_id']] = {
                    'expiry': datetime.fromisoformat(row['expiry']),
                    'plan': row['plan'] or 'basic'
                }
            except ValueError:
                pass
        c.execute('SELECT user_id, file_name, file_type FROM user_files')
        for row in c.fetchall():
            uid = row['user_id']
            if uid not in user_files:
                user_files[uid] = []
            user_files[uid].append((row['file_name'], row['file_type']))
        c.execute('SELECT user_id FROM active_users')
        active_users.update(r['user_id'] for r in c.fetchall())
        c.execute('SELECT user_id FROM admins')
        admin_ids.update(r['user_id'] for r in c.fetchall())
        c.execute('SELECT user_id FROM banned_users')
        banned_users.update(r['user_id'] for r in c.fetchall())
        c.execute('SELECT user_id, reason FROM user_warnings')
        for row in c.fetchall():
            user_warnings[row['user_id']] += 1
            user_warn_reasons[row['user_id']].append(row['reason'])
        conn.close()
        logger.info(f"Loaded: {len(active_users)} users, {len(user_subscriptions)} subs, "
                    f"{len(banned_users)} bans, {len(admin_ids)} admins")
    except Exception as e:
        logger.error(f"Load data error: {e}", exc_info=True)

def save_user_file_db(user_id, file_name, file_type, file_size=0):
    try:
        conn = get_db()
        conn.execute(
            'INSERT OR REPLACE INTO user_files (user_id, file_name, file_type, upload_time, file_size) VALUES (?,?,?,?,?)',
            (user_id, file_name, file_type, datetime.now().isoformat(), file_size))
        conn.commit(); conn.close()
        log_action(user_id, "FILE_UPLOAD", f"Uploaded {file_name}")
    except Exception as e:
        logger.error(f"save_user_file_db: {e}")

def remove_user_file_db(user_id, file_name):
    try:
        conn = get_db()
        conn.execute('DELETE FROM user_files WHERE user_id=? AND file_name=?', (user_id, file_name))
        conn.commit(); conn.close()
    except Exception as e:
        logger.error(f"remove_user_file_db: {e}")

def save_active_user(user_id, username=None):
    try:
        conn = get_db()
        now = datetime.now().isoformat()
        conn.execute(
            'INSERT INTO active_users (user_id, username, first_seen, last_seen) VALUES (?,?,?,?) '
            'ON CONFLICT(user_id) DO UPDATE SET last_seen=?, username=?',
            (user_id, username, now, now, now, username))
        conn.commit(); conn.close()
    except Exception as e:
        logger.error(f"save_active_user: {e}")

def log_action(user_id, action, details):
    try:
        conn = get_db()
        conn.execute(
            'INSERT INTO bot_logs (user_id, action, details, timestamp) VALUES (?,?,?,?)',
            (user_id, action, details, datetime.now().isoformat()))
        conn.commit(); conn.close()
    except Exception as e:
        logger.error(f"log_action: {e}")

def save_subscription(user_id, expiry, plan='basic'):
    try:
        conn = get_db()
        conn.execute(
            'INSERT OR REPLACE INTO subscriptions (user_id, expiry, plan) VALUES (?,?,?)',
            (user_id, expiry.isoformat(), plan))
        conn.commit(); conn.close()
    except Exception as e:
        logger.error(f"save_subscription: {e}")

def save_ban_db(user_id, reason, banned_by):
    try:
        conn = get_db()
        conn.execute(
            'INSERT OR REPLACE INTO banned_users (user_id, reason, banned_by, banned_at) VALUES (?,?,?,?)',
            (user_id, reason, banned_by, datetime.now().isoformat()))
        conn.commit(); conn.close()
    except Exception as e:
        logger.error(f"save_ban_db: {e}")

def remove_ban_db(user_id):
    try:
        conn = get_db()
        conn.execute('DELETE FROM banned_users WHERE user_id=?', (user_id,))
        conn.commit(); conn.close()
    except Exception as e:
        logger.error(f"remove_ban_db: {e}")

def save_warning_db(user_id, reason):
    try:
        conn = get_db()
        conn.execute(
            'INSERT INTO user_warnings (user_id, reason, warned_at) VALUES (?,?,?)',
            (user_id, reason, datetime.now().isoformat()))
        conn.commit(); conn.close()
    except Exception as e:
        logger.error(f"save_warning_db: {e}")

# Init
init_db()
load_data()


# ============================================================
# 🔧 HELPER FUNCTIONS
# ============================================================

def get_user_folder(user_id):
    folder = os.path.join(UPLOAD_BOTS_DIR, str(user_id))
    os.makedirs(folder, exist_ok=True)
    return folder

def get_user_file_limit(user_id):
    if user_id == OWNER_ID:
        return OWNER_LIMIT
    if user_id in admin_ids:
        return ADMIN_LIMIT
    sub = user_subscriptions.get(user_id)
    if sub and sub['expiry'] > datetime.now():
        plan = sub.get('plan', 'basic')
        return SUBSCRIPTION_PLANS.get(plan, SUBSCRIPTION_PLANS['basic'])['limit']
    return FREE_USER_LIMIT

def get_user_file_count(user_id):
    return len(user_files.get(user_id, []))

def get_user_status_label(user_id):
    if user_id == OWNER_ID:
        return "👑 Owner"
    if user_id in admin_ids:
        return "⭐ Admin"
    sub = user_subscriptions.get(user_id)
    if sub and sub['expiry'] > datetime.now():
        plan = sub.get('plan', 'basic')
        return SUBSCRIPTION_PLANS.get(plan, {}).get('label', '🌟 Premium')
    return "👤 Free"


# ============================================================
# 📦 PACKAGE INSTALLATION
# ============================================================

TELEGRAM_MODULES = {
    'telebot': 'pytelegrambotapi', 'telegram': 'python-telegram-bot',
    'pyrogram': 'pyrogram', 'telethon': 'telethon', 'aiogram': 'aiogram',
    'PIL': 'Pillow', 'cv2': 'opencv-python', 'sklearn': 'scikit-learn',
    'bs4': 'beautifulsoup4', 'dotenv': 'python-dotenv', 'yaml': 'pyyaml',
    'aiohttp': 'aiohttp', 'numpy': 'numpy', 'pandas': 'pandas',
    'requests': 'requests', 'flask': 'flask', 'django': 'django',
    'fastapi': 'fastapi',
}

def attempt_install_pip(module_name, message):
    package_name = TELEGRAM_MODULES.get(module_name.lower(), module_name)
    try:
        msg = send_spinner_animation(message.chat.id, f"Installing {package_name}...", duration=2)
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', package_name],
            capture_output=True, text=True, timeout=120, encoding='utf-8', errors='ignore')
        if result.returncode == 0:
            try:
                bot.edit_message_text(
                    f"✅ <b>Installed!</b> <code>{package_name}</code>",
                    message.chat.id, msg.message_id, parse_mode='HTML')
            except Exception:
                pass
            return True
        else:
            try:
                bot.edit_message_text(
                    f"❌ <b>Install failed:</b> <code>{result.stderr[:300]}</code>",
                    message.chat.id, msg.message_id, parse_mode='HTML')
            except Exception:
                pass
            return False
    except subprocess.TimeoutExpired:
        bot.send_message(message.chat.id, f"⏱️ Install timed out: {package_name}")
        return False
    except Exception as e:
        logger.error(f"Install error: {e}")
        return False

def attempt_install_npm(module_name, user_folder, message):
    try:
        msg = send_spinner_animation(message.chat.id, f"Installing npm: {module_name}...", duration=2)
        result = subprocess.run(
            ['npm', 'install', module_name], capture_output=True, text=True,
            cwd=user_folder, timeout=120, encoding='utf-8', errors='ignore')
        if result.returncode == 0:
            try:
                bot.edit_message_text(
                    f"✅ <b>NPM Installed:</b> <code>{module_name}</code>",
                    message.chat.id, msg.message_id, parse_mode='HTML')
            except Exception:
                pass
            return True
        return False
    except FileNotFoundError:
        bot.send_message(message.chat.id, "❌ Node.js not found!")
        return False
    except Exception as e:
        logger.error(f"NPM install error: {e}")
        return False


# ============================================================
# 🤖 SCRIPT RUNNING (Merged Python + JS into one function)
# ============================================================

def run_script_generic(script_path, script_owner_id, user_folder, file_name, message_obj,
                       script_type='py', attempt=1):
    """Unified script runner for Python and Node.js"""
    max_attempts = 3
    if attempt > max_attempts:
        bot.send_message(message_obj.chat.id,
            f"❌ Failed to run <code>{file_name}</code> after {max_attempts} attempts.")
        return

    script_key = f"{script_owner_id}_{file_name}"
    is_py = (script_type == 'py')
    runner = [sys.executable] if is_py else ['node']
    lang_label = "Python 🐍" if is_py else "Node.js 🟨"

    try:
        if not os.path.exists(script_path):
            bot.send_message(message_obj.chat.id, f"❌ File not found: <code>{file_name}</code>")
            return

        # Python syntax check
        if is_py:
            check = subprocess.run(
                [sys.executable, '-c', f'import ast; ast.parse(open("{script_path}").read())'],
                capture_output=True, text=True, timeout=10)
            if check.returncode != 0:
                bot.send_message(message_obj.chat.id,
                    f"⚠️ <b>Syntax Error:</b>\n<code>{check.stderr[:400]}</code>",
                    parse_mode='HTML')
                return

        start_msg = (
            f"╔══════════════════════════════════════╗\n"
            f"║      🚀 <b>AMMAR DEVX: STARTING</b> 🚀       ║\n"
            f"╠══════════════════════════════════════╣\n"
            f"║ 📄 File: <code>{file_name[:25]}</code>\n"
            f"║ 🔤 Lang: {lang_label}\n"
            f"║ 👤 User: {script_owner_id}\n"
            f"║ 🔄 Attempt: {attempt}/{max_attempts}\n"
            f"╚══════════════════════════════════════╝")
        msg = send_animated_message(message_obj.chat.id, start_msg, "run", duration=2)

        log_file_path = os.path.join(LOGS_DIR, f"{script_key}.log")
        log_file = open(log_file_path, 'w', encoding='utf-8', errors='ignore')

        process = subprocess.Popen(
            runner + [script_path], cwd=user_folder,
            stdout=log_file, stderr=subprocess.STDOUT,
            text=True, encoding='utf-8', errors='ignore')

        bot_scripts[script_key] = {
            'process': process, 'file_name': file_name, 'user_id': script_owner_id,
            'start_time': datetime.now(), 'log_file': log_file,
            'log_path': log_file_path, 'script_key': script_key,
            'script_path': script_path, 'type': script_type
        }

        time.sleep(2)
        if process.poll() is None:
            success = (
                f"╔══════════════════════════════════════╗\n"
                f"║     ✅ <b>AMMAR DEVX: RUNNING</b> ✅        ║\n"
                f"╠══════════════════════════════════════╣\n"
                f"║ 📄 <b>File:</b> <code>{file_name[:25]}</code>\n"
                f"║ 🆔 <b>PID:</b> {process.pid}\n"
                f"║ ⏱️ <b>Started:</b> {datetime.now().strftime('%H:%M:%S')}\n"
                f"╚══════════════════════════════════════╝")
            try:
                bot.edit_message_text(success, message_obj.chat.id, msg.message_id, parse_mode='HTML')
            except Exception:
                bot.send_message(message_obj.chat.id, success, parse_mode='HTML')
            log_action(script_owner_id, "SCRIPT_START", f"Started {file_name} (PID:{process.pid})")
            track_script_run()
        else:
            log_file.close()
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                error_output = f.read()[-1000:]

            # Auto-install missing modules
            pattern = r"ModuleNotFoundError: No module named '(.+?)'" if is_py else r"Cannot find module '(.+?)'"
            match = re.search(pattern, error_output)
            if match:
                module = match.group(1).strip()
                installed = (attempt_install_pip(module, message_obj) if is_py
                             else attempt_install_npm(module, user_folder, message_obj))
                if installed:
                    time.sleep(1)
                    run_script_generic(script_path, script_owner_id, user_folder,
                                       file_name, message_obj, script_type, attempt + 1)
                    return

            error_msg = (
                f"╔══════════════════════════════════════╗\n"
                f"║     ❌ <b>AMMAR DEVX: FAILED</b> ❌         ║\n"
                f"╠══════════════════════════════════════╣\n"
                f"║ 📄 <b>File:</b> <code>{file_name[:25]}</code>\n"
                f"║ ❗ <b>Exit Code:</b> {process.returncode}\n"
                f"╠══════════════════════════════════════╣\n"
                f"<code>{error_output[:400]}</code>\n"
                f"╚══════════════════════════════════════╝")
            try:
                bot.edit_message_text(error_msg, message_obj.chat.id, msg.message_id, parse_mode='HTML')
            except Exception:
                bot.send_message(message_obj.chat.id, error_msg, parse_mode='HTML')
            cleanup_script(script_key)
            track_error()

    except Exception as e:
        logger.error(f"run_script_generic error: {e}", exc_info=True)
        bot.send_message(message_obj.chat.id, f"❌ Error: {str(e)[:200]}")
        track_error()

# Aliases for backward compat
def run_script(script_path, owner_id, folder, name, msg_obj, attempt=1):
    run_script_generic(script_path, owner_id, folder, name, msg_obj, 'py', attempt)

def run_js_script(script_path, owner_id, folder, name, msg_obj, attempt=1):
    run_script_generic(script_path, owner_id, folder, name, msg_obj, 'js', attempt)


# ============================================================
# ⌨️ KEYBOARD LAYOUTS
# ============================================================

def get_main_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    if user_id == OWNER_ID or user_id in admin_ids:
        markup.row("📢 Updates Channel", "📤 Upload File")
        markup.row("📂 Check Files", "🟢 Running Bots")
        markup.row("⚡ Bot Speed", "📊 Statistics")
        markup.row("💳 Subscriptions", "📢 Broadcast")
        markup.row("🔒 Lock Bot", "👑 Admin Panel")
        markup.row("📈 Analytics", "📞 Contact Owner")
    else:
        markup.row("📢 Updates Channel", "📤 Upload File")
        markup.row("📂 Check Files", "🟢 My Running Bots")
        markup.row("⚡ Bot Speed", "📊 My Stats")
        markup.row("💰 Buy Subscription", "📞 Contact Owner")
    return markup

def get_file_actions_keyboard(file_name, is_running=False):
    markup = types.InlineKeyboardMarkup(row_width=2)
    if is_running:
        markup.add(
            types.InlineKeyboardButton("🛑 Stop", callback_data=f"stop_{file_name}"),
            types.InlineKeyboardButton("📋 Logs", callback_data=f"logs_{file_name}"))
        markup.add(types.InlineKeyboardButton("🔄 Restart", callback_data=f"restart_{file_name}"))
    else:
        markup.add(
            types.InlineKeyboardButton("▶️ Run", callback_data=f"run_{file_name}"),
            types.InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_{file_name}"))
        markup.add(
            types.InlineKeyboardButton("📥 Download", callback_data=f"download_{file_name}"),
            types.InlineKeyboardButton("📝 Edit", callback_data=f"edit_{file_name}"))
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_files"))
    return markup


# ============================================================
# 📨 COMMAND HANDLERS
# ============================================================

@bot.message_handler(commands=['start'])
@security_check
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    first_name = message.from_user.first_name or "User"
    is_new = user_id not in active_users
    active_users.add(user_id)
    save_active_user(user_id, username)
    log_action(user_id, "START", "Bot started")
    track_command('start', user_id)
    if is_new:
        notify_new_user(user_id, username, first_name)

    limit = get_user_file_limit(user_id)
    limit_str = str(int(limit)) if limit != float('inf') else '∞'
    welcome = (
        f"╔══════════════════════════════════════╗\n"
        f"║    🤖 <b>AMMAR DEVX 🦁</b>                 ║\n"
        f"╠══════════════════════════════════════╣\n"
        f"║  👋 Welcome, <b>{first_name}</b>!\n"
        f"║  📤 Upload & Host your bot files\n"
        f"║  🚀 Run Python & Node.js scripts\n"
        f"║  📊 Monitor your running bots\n"
        f"║  💾 Manage your files easily\n"
        f"╠══════════════════════════════════════╣\n"
        f"║  📌 <b>Your Info:</b>\n"
        f"║  📁 Files: {get_user_file_count(user_id)}/{limit_str}\n"
        f"║  💳 Status: {get_user_status_label(user_id)}\n"
        f"║  ⚠️ Warnings: {user_warnings.get(user_id, 0)}/{MAX_WARNINGS}\n"
        f"╚══════════════════════════════════════╝\n"
        f"Use the buttons below to navigate! ⬇️")
    send_animated_message(message.chat.id, welcome, "loading", duration=2)
    bot.send_message(message.chat.id, "Choose an option:", reply_markup=get_main_keyboard(user_id))

@bot.message_handler(commands=['help'])
@security_check
def help_command(message):
    track_command('help', message.from_user.id)
    help_text = (
        "╔══════════════════════════════════════╗\n"
        "║       📚 <b>AMMAR DEVX HELP</b> 📚          ║\n"
        "╠══════════════════════════════════════╣\n"
        "║ <b>📤 File Management:</b>\n"
        "║ • /upload - Upload a file\n"
        "║ • /files - View your files\n"
        "║ • /delete - Delete a file\n"
        "║\n"
        "║ <b>🤖 Bot Control:</b>\n"
        "║ • /run - Run a script\n"
        "║ • /stop - Stop a script\n"
        "║ • /logs - View script logs\n"
        "║ • /running - See running scripts\n"
        "║\n"
        "║ <b>💰 Subscription:</b>\n"
        "║ • /buy - View & buy plans\n"
        "║ • /status - Your account status\n"
        "║\n"
        "║ <b>📊 Info:</b>\n"
        "║ • /stats - System stats\n"
        "║ • /speed - Bot speed\n"
        "║ • /analytics - Usage analytics (admin)\n"
        "╚══════════════════════════════════════╝")
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

@bot.message_handler(commands=['stats', 'statistics'])
@security_check
def stats_command(message):
    track_command('stats', message.from_user.id)
    msg = send_spinner_animation(message.chat.id, "Gathering stats...", duration=2)
    try:
        bot.edit_message_text(create_system_stats_message(), message.chat.id, msg.message_id, parse_mode='HTML')
    except Exception:
        bot.send_message(message.chat.id, create_system_stats_message(), parse_mode='HTML')

@bot.message_handler(commands=['speed'])
@security_check
def speed_command(message):
    track_command('speed', message.from_user.id)
    msg = send_spinner_animation(message.chat.id, "Testing speed...", duration=2)
    start = time.time()
    bot.get_me()
    latency = (time.time() - start) * 1000
    cpu = psutil.cpu_percent()
    memory = psutil.virtual_memory().percent
    grade = "🟢 Excellent!" if latency < 100 else "🟡 Good" if latency < 500 else "🔴 Slow"
    speed_text = (
        f"╔══════════════════════════════════════╗\n"
        f"║        ⚡ <b>AMMAR DEVX SPEED</b> ⚡        ║\n"
        f"╠══════════════════════════════════════╣\n"
        f"║  🏓 <b>Latency:</b> {latency:.2f}ms\n"
        f"║  🖥️ <b>CPU:</b> {cpu}%\n"
        f"║  🧠 <b>Memory:</b> {memory}%\n"
        f"║  ⏱️ <b>Uptime:</b> {get_uptime()}\n"
        f"║  {grade}\n"
        f"╚══════════════════════════════════════╝")
    try:
        bot.edit_message_text(speed_text, message.chat.id, msg.message_id, parse_mode='HTML')
    except Exception:
        bot.send_message(message.chat.id, speed_text, parse_mode='HTML')

@bot.message_handler(commands=['running'])
@security_check
def running_command(message):
    track_command('running', message.from_user.id)
    user_id = message.from_user.id
    msg = send_spinner_animation(message.chat.id, "Fetching bots...", duration=1)
    running_bots = []
    for sk, info in bot_scripts.items():
        if is_bot_running_check(sk):
            if user_id == OWNER_ID or user_id in admin_ids or info.get('user_id') == user_id:
                uptime_s = str(datetime.now() - info.get('start_time', datetime.now())).split('.')[0]
                running_bots.append({
                    'key': sk, 'file': info.get('file_name', 'Unknown'),
                    'user': info.get('user_id', '?'),
                    'pid': info['process'].pid if info.get('process') else 'N/A',
                    'uptime': uptime_s
                })
    if running_bots:
        text = "╔══════════════════════════════════════╗\n║      🟢 <b>RUNNING BOTS</b> 🟢           ║\n╠══════════════════════════════════════╣\n"
        for i, b in enumerate(running_bots, 1):
            text += f"║ {i}. 📄 <code>{b['file'][:20]}</code>\n║    👤 {b['user']} | 🆔 {b['pid']} | ⏱️ {b['uptime']}\n║ ──────────────────────────────────\n"
        text += "╚══════════════════════════════════════╝"
    else:
        text = "╔══════════════════════════════════════╗\n║      🔴 <b>NO BOTS RUNNING</b> 🔴        ║\n╠══════════════════════════════════════╣\n║  Upload a file and run it!\n╚══════════════════════════════════════╝"
    try:
        bot.edit_message_text(text, message.chat.id, msg.message_id, parse_mode='HTML')
    except Exception:
        bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['status'])
@security_check
def status_command(message):
    track_command('status', message.from_user.id)
    user_id = message.from_user.id
    sub = user_subscriptions.get(user_id)
    limit = get_user_file_limit(user_id)
    limit_str = str(int(limit)) if limit != float('inf') else '∞'
    if sub and sub['expiry'] > datetime.now():
        remaining = (sub['expiry'] - datetime.now()).days
        plan_label = SUBSCRIPTION_PLANS.get(sub.get('plan','basic'), {}).get('label', '🌟 Premium')
        sub_info = f"{plan_label} — {remaining} days left\n║  Expires: {sub['expiry'].strftime('%Y-%m-%d')}"
    else:
        sub_info = "👤 Free Plan\n║  Upgrade: /buy"
    running = len([k for k, v in bot_scripts.items()
                   if v.get('user_id') == user_id and is_bot_running_check(k)])
    text = (
        f"╔══════════════════════════════════════╗\n"
        f"║       👤 <b>YOUR ACCOUNT STATUS</b>         ║\n"
        f"╠══════════════════════════════════════╣\n"
        f"║  🆔 ID: <code>{user_id}</code>\n"
        f"║  🏷️ Role: {get_user_status_label(user_id)}\n"
        f"║  💳 Subscription: {sub_info}\n"
        f"║  📁 Files: {get_user_file_count(user_id)}/{limit_str}\n"
        f"║  🤖 Running: {running}\n"
        f"║  ⚠️ Warnings: {user_warnings.get(user_id, 0)}/{MAX_WARNINGS}\n"
        f"╚══════════════════════════════════════╝")
    bot.send_message(message.chat.id, text, parse_mode='HTML')

# ── 💰 SUBSCRIPTION / BUY ────────────────────────────────────

@bot.message_handler(commands=['buy'])
@security_check
def buy_command(message):
    track_command('buy', message.from_user.id)
    text = (
        "╔══════════════════════════════════════╗\n"
        "║     💰 <b>AMMAR DEVX PLANS</b> 💰          ║\n"
        "╠══════════════════════════════════════╣\n"
        "║  Select a plan to subscribe:\n"
        "║\n"
        "║  ⭐ Basic  — 100 PKR/mo — 15 files\n"
        "║  💎 Pro    — 250 PKR/mo — 30 files\n"
        "║  👑 Premium— 500 PKR/mo — 999 files\n"
        "╚══════════════════════════════════════╝")
    bot.send_message(message.chat.id, text, parse_mode='HTML',
                     reply_markup=get_subscription_keyboard())

@bot.message_handler(commands=['approve'])
def approve_command(message):
    """Admin: /approve <user_id>"""
    user_id = message.from_user.id
    if user_id != OWNER_ID and user_id not in admin_ids:
        bot.reply_to(message, "❌ Admin only!")
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Usage: /approve <user_id>")
        return
    try:
        target = int(parts[1])
    except ValueError:
        bot.reply_to(message, "❌ Invalid user ID")
        return
    success, result = approve_payment(target, user_id)
    if success:
        send_animated_message(message.chat.id,
            f"✅ <b>Payment approved!</b>\nUser: {target}\nExpiry: {result.strftime('%Y-%m-%d')}",
            "loading", duration=1)
        try:
            bot.send_message(target,
                "🎉 <b>Subscription Activated!</b>\n"
                "Your payment has been approved. Enjoy your plan!")
        except Exception:
            pass
    else:
        bot.reply_to(message, f"❌ {result}")

@bot.message_handler(commands=['reject'])
def reject_command(message):
    """Admin: /reject <user_id> [reason]"""
    user_id = message.from_user.id
    if user_id != OWNER_ID and user_id not in admin_ids:
        bot.reply_to(message, "❌ Admin only!")
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2:
        bot.reply_to(message, "Usage: /reject <user_id> [reason]")
        return
    try:
        target = int(parts[1])
    except ValueError:
        bot.reply_to(message, "❌ Invalid user ID")
        return
    reason = parts[2] if len(parts) > 2 else "Rejected by admin"
    if reject_payment(target, reason):
        bot.reply_to(message, f"✅ Payment rejected for {target}")
        try:
            bot.send_message(target, f"❌ <b>Payment Rejected</b>\nReason: {reason}\nContact: {YOUR_USERNAME}")
        except Exception:
            pass
    else:
        bot.reply_to(message, "❌ No pending payment found")

# ── 👤 USER MANAGEMENT ────────────────────────────────────────

@bot.message_handler(commands=['ban'])
def ban_command(message):
    """Admin: /ban <user_id> [reason]"""
    if message.from_user.id != OWNER_ID and message.from_user.id not in admin_ids:
        bot.reply_to(message, "❌ Admin only!")
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2:
        bot.reply_to(message, "Usage: /ban <user_id> [reason]")
        return
    try:
        target = int(parts[1])
    except ValueError:
        bot.reply_to(message, "❌ Invalid user ID")
        return
    if target == OWNER_ID:
        bot.reply_to(message, "❌ Cannot ban owner!")
        return
    reason = parts[2] if len(parts) > 2 else "Banned by admin"
    ban_user(target, reason, message.from_user.id)
    bot.reply_to(message, f"🚫 User <code>{target}</code> banned.\nReason: {reason}", parse_mode='HTML')
    try:
        bot.send_message(target, f"🚫 <b>You have been banned.</b>\nReason: {reason}\nAppeal: {YOUR_USERNAME}")
    except Exception:
        pass

@bot.message_handler(commands=['unban'])
def unban_command(message):
    """Admin: /unban <user_id>"""
    if message.from_user.id != OWNER_ID and message.from_user.id not in admin_ids:
        bot.reply_to(message, "❌ Admin only!")
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Usage: /unban <user_id>")
        return
    try:
        target = int(parts[1])
    except ValueError:
        bot.reply_to(message, "❌ Invalid user ID")
        return
    unban_user(target)
    bot.reply_to(message, f"✅ User <code>{target}</code> unbanned.", parse_mode='HTML')
    try:
        bot.send_message(target, "✅ <b>You have been unbanned!</b> Welcome back.")
    except Exception:
        pass

@bot.message_handler(commands=['warn'])
def warn_command(message):
    """Admin: /warn <user_id> [reason]"""
    if message.from_user.id != OWNER_ID and message.from_user.id not in admin_ids:
        bot.reply_to(message, "❌ Admin only!")
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2:
        bot.reply_to(message, "Usage: /warn <user_id> [reason]")
        return
    try:
        target = int(parts[1])
    except ValueError:
        bot.reply_to(message, "❌ Invalid user ID")
        return
    reason = parts[2] if len(parts) > 2 else "Rule violation"
    count, auto_banned = warn_user(target, reason)
    if auto_banned:
        bot.reply_to(message,
            f"⚠️ User <code>{target}</code> warned ({count}/{MAX_WARNINGS}) and <b>auto-banned!</b>",
            parse_mode='HTML')
    else:
        bot.reply_to(message,
            f"⚠️ User <code>{target}</code> warned. ({count}/{MAX_WARNINGS})",
            parse_mode='HTML')
    try:
        bot.send_message(target,
            f"⚠️ <b>Warning {count}/{MAX_WARNINGS}</b>\nReason: {reason}\n"
            f"{'🚫 You have been auto-banned!' if auto_banned else f'Next warning = ban!'}")
    except Exception:
        pass

@bot.message_handler(commands=['addadmin'])
def addadmin_command(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ Owner only!")
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Usage: /addadmin <user_id>")
        return
    try:
        target = int(parts[1])
    except ValueError:
        bot.reply_to(message, "❌ Invalid ID")
        return
    admin_ids.add(target)
    conn = get_db()
    conn.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (target,))
    conn.commit(); conn.close()
    bot.reply_to(message, f"✅ <code>{target}</code> is now admin.", parse_mode='HTML')

@bot.message_handler(commands=['removeadmin'])
def removeadmin_command(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ Owner only!")
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Usage: /removeadmin <user_id>")
        return
    try:
        target = int(parts[1])
    except ValueError:
        bot.reply_to(message, "❌ Invalid ID")
        return
    admin_ids.discard(target)
    conn = get_db()
    conn.execute('DELETE FROM admins WHERE user_id=?', (target,))
    conn.commit(); conn.close()
    bot.reply_to(message, f"✅ <code>{target}</code> removed from admins.", parse_mode='HTML')

@bot.message_handler(commands=['userinfo'])
def userinfo_command(message):
    """Admin: get info about a user"""
    if message.from_user.id != OWNER_ID and message.from_user.id not in admin_ids:
        bot.reply_to(message, "❌ Admin only!")
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Usage: /userinfo <user_id>")
        return
    try:
        target = int(parts[1])
    except ValueError:
        bot.reply_to(message, "❌ Invalid ID")
        return
    sub = user_subscriptions.get(target)
    sub_str = f"{sub['expiry'].strftime('%Y-%m-%d')}" if sub and sub['expiry'] > datetime.now() else "None"
    limit = get_user_file_limit(target)
    limit_str = str(int(limit)) if limit != float('inf') else '∞'
    running = len([k for k, v in bot_scripts.items()
                   if v.get('user_id') == target and is_bot_running_check(k)])
    text = (
        f"╔══════════════════════════════════════╗\n"
        f"║       🔍 <b>USER INFO</b>                   ║\n"
        f"╠══════════════════════════════════════╣\n"
        f"║  🆔 ID: <code>{target}</code>\n"
        f"║  🏷️ Role: {get_user_status_label(target)}\n"
        f"║  💳 Sub Expiry: {sub_str}\n"
        f"║  📁 Files: {get_user_file_count(target)}/{limit_str}\n"
        f"║  🤖 Running Bots: {running}\n"
        f"║  ⚠️ Warnings: {user_warnings.get(target, 0)}/{MAX_WARNINGS}\n"
        f"║  🚫 Banned: {'Yes' if target in banned_users else 'No'}\n"
        f"╚══════════════════════════════════════╝")
    bot.send_message(message.chat.id, text, parse_mode='HTML')

# ── 📊 ANALYTICS ─────────────────────────────────────────────

@bot.message_handler(commands=['analytics'])
def analytics_command(message):
    if message.from_user.id != OWNER_ID and message.from_user.id not in admin_ids:
        bot.reply_to(message, "❌ Admin only!")
        return
    msg = send_spinner_animation(message.chat.id, "Gathering analytics...", duration=1)
    report = get_analytics_report()
    try:
        bot.edit_message_text(report, message.chat.id, msg.message_id, parse_mode='HTML')
    except Exception:
        bot.send_message(message.chat.id, report, parse_mode='HTML')

# ── 🔒 LOCK / BROADCAST ──────────────────────────────────────

@bot.message_handler(commands=['lock'])
def lock_command(message):
    global bot_locked
    if message.from_user.id != OWNER_ID and message.from_user.id not in admin_ids:
        bot.reply_to(message, "❌ No permission!")
        return
    bot_locked = not bot_locked
    status = "🔒 LOCKED" if bot_locked else "🔓 UNLOCKED"
    send_animated_message(message.chat.id,
        f"╔══════════════════════════════════════╗\n"
        f"║         🔐 <b>BOT STATUS</b> 🔐              ║\n"
        f"╠══════════════════════════════════════╣\n"
        f"║  Status: {status}\n"
        f"║  By: {message.from_user.first_name}\n"
        f"║  Time: {datetime.now().strftime('%H:%M:%S')}\n"
        f"╚══════════════════════════════════════╝", "terminal", duration=1)

@bot.message_handler(commands=['broadcast'])
def broadcast_command(message):
    if message.from_user.id != OWNER_ID and message.from_user.id not in admin_ids:
        bot.reply_to(message, "❌ No permission!")
        return
    msg = bot.reply_to(message, "📢 Send the message to broadcast:")
    bot.register_next_step_handler(msg, process_broadcast)

def process_broadcast(message):
    broadcast_text = message.text
    if not broadcast_text:
        bot.reply_to(message, "❌ Send a text message!")
        return
    progress_msg = bot.send_message(message.chat.id, "📢 Starting broadcast...")
    success = failed = 0
    total = len(active_users)
    for i, uid in enumerate(active_users):
        try:
            formatted = (
                f"╔══════════════════════════════════════╗\n"
                f"║      📢 <b>AMMAR DEVX BROADCAST</b> 📢    ║\n"
                f"╠══════════════════════════════════════╣\n"
                f"║\n{broadcast_text}\n║\n"
                f"╚══════════════════════════════════════╝")
            bot.send_message(uid, formatted, parse_mode='HTML')
            success += 1
        except Exception:
            failed += 1
        if total > 0 and (i + 1) % 10 == 0:
            pct = int((i + 1) / total * 100)
            bar = "🟩" * (pct // 25) + "⬜" * (4 - pct // 25)
            try:
                bot.edit_message_text(
                    f"⚙️ Broadcasting... ({pct}%)\n[{bar}]",
                    message.chat.id, progress_msg.message_id)
            except Exception:
                pass
    result = (
        f"╔══════════════════════════════════════╗\n"
        f"║     ✅ <b>BROADCAST COMPLETE</b> ✅         ║\n"
        f"╠══════════════════════════════════════╣\n"
        f"║  📤 Total: {total}\n"
        f"║  ✅ Success: {success}\n"
        f"║  ❌ Failed: {failed}\n"
        f"╚══════════════════════════════════════╝")
    try:
        bot.edit_message_text(result, message.chat.id, progress_msg.message_id, parse_mode='HTML')
    except Exception:
        bot.send_message(message.chat.id, result, parse_mode='HTML')

@bot.message_handler(commands=['subscribe', 'sub'])
def subscribe_command(message):
    if message.from_user.id != OWNER_ID and message.from_user.id not in admin_ids:
        bot.reply_to(message, "❌ No permission!")
        return
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "Usage: /subscribe <user_id> <days> [plan]")
        return
    try:
        target = int(parts[1])
        days = int(parts[2])
        plan = parts[3] if len(parts) > 3 and parts[3] in SUBSCRIPTION_PLANS else 'basic'
    except ValueError:
        bot.reply_to(message, "❌ Invalid user ID or days!")
        return
    expiry = datetime.now() + timedelta(days=days)
    user_subscriptions[target] = {'expiry': expiry, 'plan': plan}
    save_subscription(target, expiry, plan)
    plan_label = SUBSCRIPTION_PLANS[plan]['label']
    send_animated_message(message.chat.id,
        f"✅ <b>Subscribed!</b>\n👤 User: {target}\n📦 Plan: {plan_label}\n📅 Days: {days}\n⏰ Expires: {expiry.strftime('%Y-%m-%d')}",
        "loading", duration=1)
    try:
        bot.send_message(target,
            f"🎉 <b>You've been subscribed!</b>\n"
            f"Plan: {plan_label}\nDays: {days}\nExpires: {expiry.strftime('%Y-%m-%d')}")
    except Exception:
        pass

@bot.message_handler(commands=['stopall'])
def stopall_command(message):
    if message.from_user.id != OWNER_ID and message.from_user.id not in admin_ids:
        bot.reply_to(message, "❌ Admin only!")
        return
    stopped = 0
    for sk in list(bot_scripts.keys()):
        try:
            kill_process_tree(bot_scripts[sk])
            cleanup_script(sk)
            stopped += 1
        except Exception:
            pass
    bot.reply_to(message, f"✅ Stopped {stopped} bot(s).")

@bot.message_handler(commands=['notify'])
def notify_command(message):
    """Admin: toggle notification settings"""
    if message.from_user.id != OWNER_ID and message.from_user.id not in admin_ids:
        bot.reply_to(message, "❌ Admin only!")
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, val in notify_settings.items():
        if key == 'report_time':
            continue
        icon = "✅" if val else "❌"
        markup.add(types.InlineKeyboardButton(
            f"{icon} {key.replace('_', ' ').title()}",
            callback_data=f"notify_toggle_{key}"))
    bot.send_message(message.chat.id, "🔔 <b>Notification Settings:</b>", parse_mode='HTML',
                     reply_markup=markup)


# ============================================================
# 💬 TEXT MESSAGE HANDLER
# ============================================================

@bot.message_handler(content_types=['text'])
@security_check
def handle_text(message):
    user_id = message.from_user.id
    text = message.text
    active_users.add(user_id)
    track_command(text, user_id)

    if text == "📢 Updates Channel":
        bot.send_message(message.chat.id, f"📢 Join updates:\n{UPDATE_CHANNEL}")
    elif text == "📤 Upload File":
        handle_upload_request(message)
    elif text == "📂 Check Files":
        show_user_files(message)
    elif text in ("🟢 Running Bots", "🟢 My Running Bots"):
        running_command(message)
    elif text == "⚡ Bot Speed":
        speed_command(message)
    elif text in ("📊 Statistics", "📊 My Stats"):
        stats_command(message)
    elif text == "💳 Subscriptions":
        show_subscriptions(message)
    elif text == "📢 Broadcast":
        broadcast_command(message)
    elif text == "🔒 Lock Bot":
        lock_command(message)
    elif text == "👑 Admin Panel":
        show_admin_panel(message)
    elif text == "📈 Analytics":
        analytics_command(message)
    elif text == "💰 Buy Subscription":
        buy_command(message)
    elif text == "📞 Contact Owner":
        bot.send_message(message.chat.id, f"📞 Contact: {YOUR_USERNAME}")


def handle_upload_request(message):
    user_id = message.from_user.id
    count = get_user_file_count(user_id)
    limit = get_user_file_limit(user_id)
    limit_str = str(int(limit)) if limit != float('inf') else '∞'
    if count >= limit:
        bot.reply_to(message,
            f"❌ File limit reached! ({count}/{limit_str})\n"
            f"💰 Upgrade plan: /buy")
        return
    bot.send_message(message.chat.id,
        f"╔══════════════════════════════════════╗\n"
        f"║       📤 <b>AMMAR DEVX: UPLOAD</b> 📤      ║\n"
        f"╠══════════════════════════════════════╣\n"
        f"║  Send your file now!\n"
        f"║  Supported: .py .js .zip .json .txt .env .yml\n"
        f"║  Max size: {MAX_FILE_SIZE_MB}MB\n"
        f"║  Files: {count}/{limit_str}\n"
        f"╚══════════════════════════════════════╝", parse_mode='HTML')

def show_user_files(message):
    user_id = message.from_user.id
    msg = send_spinner_animation(message.chat.id, "Loading files...", duration=1)
    files = user_files.get(user_id, [])
    if not files:
        text = "╔══════════════════════════════════════╗\n║       📂 <b>YOUR FILES</b> 📂            ║\n╠══════════════════════════════════════╣\n║  No files yet! Use 📤 Upload File.\n╚══════════════════════════════════════╝"
        try:
            bot.edit_message_text(text, message.chat.id, msg.message_id, parse_mode='HTML')
        except Exception:
            bot.send_message(message.chat.id, text, parse_mode='HTML')
        return
    text = "╔══════════════════════════════════════╗\n║       📂 <b>YOUR FILES</b> 📂            ║\n╠══════════════════════════════════════╣\n"
    markup = types.InlineKeyboardMarkup(row_width=2)
    for i, (fname, ftype) in enumerate(files, 1):
        running = is_bot_running(user_id, fname)
        status = "🟢" if running else "🔴"
        icon = "🐍" if ftype == "py" else "🟨" if ftype == "js" else "📦"
        text += f"║ {i}. {status} {icon} <code>{fname[:25]}</code>\n"
        markup.add(types.InlineKeyboardButton(f"{status} {fname[:15]}", callback_data=f"file_{fname}"))
    text += "╚══════════════════════════════════════╝\nSelect a file:"
    try:
        bot.edit_message_text(text, message.chat.id, msg.message_id, parse_mode='HTML', reply_markup=markup)
    except Exception:
        bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

def show_subscriptions(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID and user_id not in admin_ids:
        bot.reply_to(message, "❌ Admin only!")
        return
    active_subs = {uid: d for uid, d in user_subscriptions.items() if d['expiry'] > datetime.now()}
    text = (
        f"╔══════════════════════════════════════╗\n"
        f"║     💳 <b>SUBSCRIPTIONS</b> 💳              ║\n"
        f"╠══════════════════════════════════════╣\n"
        f"║  Active: {len(active_subs)}\n"
        f"║  Total Ever: {len(user_subscriptions)}\n"
        f"║  Pending Payments: {len(pending_payments)}\n║\n")
    for uid, d in list(active_subs.items())[:10]:
        remaining = (d['expiry'] - datetime.now()).days
        plan = d.get('plan', 'basic')
        text += f"║  👤 {uid} [{plan}]: {remaining}d left\n"
    text += "╠══════════════════════════════════════╣\n║  /subscribe <id> <days> [plan]\n╚══════════════════════════════════════╝"
    bot.send_message(message.chat.id, text, parse_mode='HTML')

def show_admin_panel(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID and user_id not in admin_ids:
        bot.reply_to(message, "❌ Admin only!")
        return
    running = len([k for k in bot_scripts if is_bot_running_check(k)])
    active_subs = len([u for u, d in user_subscriptions.items() if d['expiry'] > datetime.now()])
    text = (
        f"╔══════════════════════════════════════╗\n"
        f"║       👑 <b>ADMIN PANEL</b> 👑              ║\n"
        f"╠══════════════════════════════════════╣\n"
        f"║  📊 Users: {len(active_users)} | Subs: {active_subs}\n"
        f"║  🤖 Running: {running} | Admins: {len(admin_ids)}\n"
        f"║  🚫 Banned: {len(banned_users)} | Pending Pay: {len(pending_payments)}\n"
        f"╠══════════════════════════════════════╣\n"
        f"║  <b>Commands:</b>\n"
        f"║  /ban /unban /warn /userinfo\n"
        f"║  /broadcast /subscribe /stopall\n"
        f"║  /addadmin /removeadmin\n"
        f"║  /approve /reject /analytics /notify\n"
        f"╚══════════════════════════════════════╝")
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🛑 Stop All", callback_data="admin_stopall"),
        types.InlineKeyboardButton("🔄 Refresh", callback_data="admin_refresh"))
    markup.add(
        types.InlineKeyboardButton("📊 Full Stats", callback_data="admin_fullstats"),
        types.InlineKeyboardButton("📋 View Logs", callback_data="admin_logs"))
    markup.add(
        types.InlineKeyboardButton("📈 Analytics", callback_data="admin_analytics"),
        types.InlineKeyboardButton("💰 Payments", callback_data="admin_payments"))
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)


# ============================================================
# 📁 FILE UPLOAD HANDLER
# ============================================================

@bot.message_handler(content_types=['document'])
@security_check
def handle_document(message):
    user_id = message.from_user.id
    count = get_user_file_count(user_id)
    limit = get_user_file_limit(user_id)
    limit_str = str(int(limit)) if limit != float('inf') else '∞'

    if count >= limit:
        bot.reply_to(message, f"❌ File limit! ({count}/{limit_str})\n💰 Upgrade: /buy")
        return

    file_name = message.document.file_name
    file_size = message.document.file_size
    file_ext = file_name.split('.')[-1].lower() if '.' in file_name else ''

    # Size check
    if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        bot.reply_to(message, f"❌ File too large! Max: {MAX_FILE_SIZE_MB}MB")
        return

    allowed = ['py', 'js', 'zip', 'json', 'txt', 'env', 'yml', 'yaml']
    if file_ext not in allowed:
        bot.reply_to(message, f"❌ Unsupported type: .{file_ext}")
        return

    upload_text = (
        f"╔══════════════════════════════════════╗\n"
        f"║      📤 <b>AMMAR DEVX: UPLOADING</b> 📤     ║\n"
        f"╠══════════════════════════════════════╣\n"
        f"║  📄 File: <code>{file_name[:25]}</code>\n"
        f"║  📦 Size: {format_size(file_size)}\n║\n")
    progress_msg = bot.reply_to(message,
        upload_text + "║  ⏳ Downloading...\n╚══════════════════════════════════════╝",
        parse_mode='HTML')

    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        user_folder = get_user_folder(user_id)

        if file_ext == 'zip':
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
                tmp.write(downloaded)
                tmp_path = tmp.name
            try:
                with zipfile.ZipFile(tmp_path, 'r') as zf:
                    # ✅ Security: path traversal check
                    for member in zf.namelist():
                        member_path = os.path.realpath(os.path.join(user_folder, member))
                        if not member_path.startswith(os.path.realpath(user_folder)):
                            raise Exception(f"Unsafe path in ZIP: {member}")
                    zf.extractall(user_folder)
                    extracted = []
                    for root, _, files in os.walk(user_folder):
                        for f in files:
                            if f.endswith(('.py', '.js')):
                                extracted.append(f)
                                with data_lock:
                                    if user_id not in user_files:
                                        user_files[user_id] = []
                                    if (f, f.split('.')[-1]) not in user_files[user_id]:
                                        user_files[user_id].append((f, f.split('.')[-1]))
                                        save_user_file_db(user_id, f, f.split('.')[-1], 0)
                os.unlink(tmp_path)
                success_text = upload_text + f"║  ✅ ZIP Extracted! Files: {len(extracted)}\n╚══════════════════════════════════════╝\n"
                track_upload()
            except zipfile.BadZipFile:
                bot.edit_message_text(
                    upload_text + "║  ❌ Invalid ZIP!\n╚══════════════════════════════════════╝",
                    message.chat.id, progress_msg.message_id, parse_mode='HTML')
                return
        else:
            file_path = os.path.join(user_folder, file_name)
            with open(file_path, 'wb') as f:
                f.write(downloaded)
            with data_lock:
                if user_id not in user_files:
                    user_files[user_id] = []
                user_files[user_id] = [(n, t) for n, t in user_files[user_id] if n != file_name]
                user_files[user_id].append((file_name, file_ext))
            save_user_file_db(user_id, file_name, file_ext, file_size)
            success_text = upload_text + "║  ✅ Upload Complete!\n╚══════════════════════════════════════╝\n"
            track_upload()

        markup = types.InlineKeyboardMarkup(row_width=2)
        if file_ext in ['py', 'js']:
            markup.add(
                types.InlineKeyboardButton("▶️ Run Now", callback_data=f"run_{file_name}"),
                types.InlineKeyboardButton("📂 View Files", callback_data="back_to_files"))
        else:
            markup.add(types.InlineKeyboardButton("📂 View Files", callback_data="back_to_files"))
        try:
            bot.edit_message_text(success_text, message.chat.id, progress_msg.message_id,
                                  parse_mode='HTML', reply_markup=markup)
        except Exception:
            bot.send_message(message.chat.id, success_text, parse_mode='HTML', reply_markup=markup)

    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        track_error()
        try:
            bot.edit_message_text(
                upload_text + f"║  ❌ Error: {str(e)[:40]}\n╚══════════════════════════════════════╝",
                message.chat.id, progress_msg.message_id, parse_mode='HTML')
        except Exception:
            bot.reply_to(message, f"❌ Upload failed: {str(e)[:100]}")


# ============================================================
# 🔘 CALLBACK QUERY HANDLER
# ============================================================

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    data = call.data

    if is_banned(user_id):
        bot.answer_callback_query(call.id, "🚫 You are banned.")
        return

    try:
        # File actions
        if data.startswith("file_"):
            show_file_actions(call, data[5:])
        elif data.startswith("run_"):
            run_user_script(call, data[4:])
        elif data.startswith("stop_"):
            stop_user_script(call, data[5:])
        elif data.startswith("delete_"):
            delete_user_file(call, data[7:])
        elif data.startswith("download_"):
            download_user_file(call, data[9:])
        elif data.startswith("logs_"):
            show_script_logs(call, data[5:])
        elif data.startswith("restart_"):
            restart_user_script(call, data[8:])
        elif data == "back_to_files":
            show_user_files_callback(call)
        # Admin panel
        elif data == "admin_stopall":
            stop_all_bots(call)
        elif data == "admin_refresh":
            refresh_admin_panel(call)
        elif data == "admin_fullstats":
            bot.answer_callback_query(call.id)
            stats_command(call.message)
        elif data == "admin_logs":
            show_admin_logs(call)
        elif data == "admin_analytics":
            bot.answer_callback_query(call.id)
            analytics_command(call.message)
        elif data == "admin_payments":
            show_pending_payments(call)
        # Delete confirm
        elif data.startswith("confirm_delete_"):
            confirm_delete_file(call, data[15:])
        elif data.startswith("cancel_delete_"):
            bot.answer_callback_query(call.id, "❌ Cancelled")
            show_user_files_callback(call)
        # Subscription buy
        elif data.startswith("buy_"):
            handle_buy_plan(call, data[4:])
        elif data == "cancel_payment":
            bot.answer_callback_query(call.id, "❌ Cancelled")
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
        # Approve/reject payment buttons
        elif data.startswith("pay_approve_"):
            target = int(data[12:])
            if user_id == OWNER_ID or user_id in admin_ids:
                success, result = approve_payment(target, user_id)
                bot.answer_callback_query(call.id, "✅ Approved!" if success else f"❌ {result}")
            else:
                bot.answer_callback_query(call.id, "❌ Admin only!")
        elif data.startswith("pay_reject_"):
            target = int(data[11:])
            if user_id == OWNER_ID or user_id in admin_ids:
                reject_payment(target)
                bot.answer_callback_query(call.id, "❌ Rejected")
                try:
                    bot.send_message(target, "❌ Your payment was rejected. Contact owner.")
                except Exception:
                    pass
            else:
                bot.answer_callback_query(call.id, "❌ Admin only!")
        # Notification toggles
        elif data.startswith("notify_toggle_"):
            key = data[14:]
            if user_id == OWNER_ID or user_id in admin_ids:
                if key in notify_settings and isinstance(notify_settings[key], bool):
                    notify_settings[key] = not notify_settings[key]
                    bot.answer_callback_query(call.id,
                        f"{'✅ Enabled' if notify_settings[key] else '❌ Disabled'}: {key}")
                    # Refresh keyboard
                    markup = types.InlineKeyboardMarkup(row_width=1)
                    for k, v in notify_settings.items():
                        if k == 'report_time':
                            continue
                        icon = "✅" if v else "❌"
                        markup.add(types.InlineKeyboardButton(
                            f"{icon} {k.replace('_', ' ').title()}",
                            callback_data=f"notify_toggle_{k}"))
                    try:
                        bot.edit_message_reply_markup(
                            call.message.chat.id, call.message.message_id, reply_markup=markup)
                    except Exception:
                        pass
            else:
                bot.answer_callback_query(call.id, "❌ Admin only!")
    except Exception as e:
        logger.error(f"Callback error: {e}", exc_info=True)
        bot.answer_callback_query(call.id, f"❌ Error: {str(e)[:50]}")


# ============================================================
# 🔘 CALLBACK HELPER FUNCTIONS
# ============================================================

def handle_buy_plan(call, plan_key):
    user_id = call.from_user.id
    if plan_key not in SUBSCRIPTION_PLANS:
        bot.answer_callback_query(call.id, "❌ Invalid plan")
        return
    payment = create_payment_request(user_id, plan_key)
    plan = SUBSCRIPTION_PLANS[plan_key]
    text = (
        f"╔══════════════════════════════════════╗\n"
        f"║     💰 <b>PAYMENT REQUEST</b> 💰            ║\n"
        f"╠══════════════════════════════════════╣\n"
        f"║  📦 Plan: {plan['label']}\n"
        f"║  💵 Amount: {plan['price']} PKR\n"
        f"║  📅 Duration: {plan['days']} days\n"
        f"║  🔖 Ref ID: <code>{payment['ref_id']}</code>\n"
        f"╠══════════════════════════════════════╣\n"
        f"║  Send payment to: {YOUR_USERNAME}\n"
        f"║  Include your Ref ID in payment note.\n"
        f"║  Admin will approve within 24 hours.\n"
        f"╚══════════════════════════════════════╝")
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='HTML')
    except Exception:
        bot.send_message(call.message.chat.id, text, parse_mode='HTML')
    bot.answer_callback_query(call.id, "✅ Payment request created!")
    # Notify owner
    if notify_settings['payment_alerts']:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ Approve", callback_data=f"pay_approve_{user_id}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"pay_reject_{user_id}"))
        try:
            bot.send_message(OWNER_ID,
                f"💰 <b>New Payment Request!</b>\n"
                f"👤 User: <code>{user_id}</code>\n"
                f"📦 Plan: {plan['label']}\n"
                f"💵 Amount: {plan['price']} PKR\n"
                f"🔖 Ref: <code>{payment['ref_id']}</code>",
                parse_mode='HTML', reply_markup=markup)
        except Exception:
            pass

def show_pending_payments(call):
    if call.from_user.id != OWNER_ID and call.from_user.id not in admin_ids:
        bot.answer_callback_query(call.id, "❌ Admin only!")
        return
    bot.answer_callback_query(call.id)
    if not pending_payments:
        bot.send_message(call.message.chat.id, "💰 No pending payments.")
        return
    for uid, pay in pending_payments.items():
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ Approve", callback_data=f"pay_approve_{uid}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"pay_reject_{uid}"))
        bot.send_message(call.message.chat.id,
            f"💰 <b>Pending Payment</b>\n"
            f"👤 User: <code>{uid}</code>\n"
            f"📦 Plan: {pay['label']}\n"
            f"💵 Amount: {pay['amount']} PKR\n"
            f"🔖 Ref: <code>{pay['ref_id']}</code>\n"
            f"🕐 Time: {pay['timestamp'].strftime('%Y-%m-%d %H:%M')}",
            parse_mode='HTML', reply_markup=markup)

def show_file_actions(call, file_name):
    user_id = call.from_user.id
    running = is_bot_running(user_id, file_name)
    ftype = next((t for n, t in user_files.get(user_id, []) if n == file_name), 'py')
    icon = "🐍" if ftype == "py" else "🟨" if ftype == "js" else "📄"
    status = "🟢 Running" if running else "🔴 Stopped"
    text = (
        f"╔══════════════════════════════════════╗\n"
        f"║       📄 <b>FILE DETAILS</b> 📄              ║\n"
        f"╠══════════════════════════════════════╣\n"
        f"║  {icon} <b>Name:</b> <code>{file_name[:25]}</code>\n"
        f"║  📁 <b>Type:</b> {ftype.upper()}\n"
        f"║  📊 <b>Status:</b> {status}\n"
        f"╚══════════════════════════════════════╝")
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                              parse_mode='HTML', reply_markup=get_file_actions_keyboard(file_name, running))
    except Exception:
        bot.send_message(call.message.chat.id, text, parse_mode='HTML',
                         reply_markup=get_file_actions_keyboard(file_name, running))
    bot.answer_callback_query(call.id)

def run_user_script(call, file_name):
    user_id = call.from_user.id
    user_folder = get_user_folder(user_id)
    script_path = os.path.join(user_folder, file_name)
    if not os.path.exists(script_path):
        bot.answer_callback_query(call.id, "❌ File not found!")
        return
    if is_bot_running(user_id, file_name):
        bot.answer_callback_query(call.id, "⚠️ Already running!")
        return
    bot.answer_callback_query(call.id, "🚀 Starting...")
    stype = 'js' if file_name.endswith('.js') else 'py'
    threading.Thread(
        target=run_script_generic,
        args=(script_path, user_id, user_folder, file_name, call.message, stype),
        daemon=True).start()

def stop_user_script(call, file_name):
    user_id = call.from_user.id
    script_key = f"{user_id}_{file_name}"
    if script_key not in bot_scripts:
        bot.answer_callback_query(call.id, "❌ Not running!")
        return
    bot.answer_callback_query(call.id, "🛑 Stopping...")
    script_info = bot_scripts.get(script_key)
    if script_info:
        kill_process_tree(script_info)
        cleanup_script(script_key)
        time.sleep(0.5)
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("▶️ Run Again", callback_data=f"run_{file_name}"),
            types.InlineKeyboardButton("🔙 Back", callback_data="back_to_files"))
        try:
            bot.edit_message_text(
                f"✅ <b>Stopped:</b> <code>{file_name}</code>",
                call.message.chat.id, call.message.message_id,
                parse_mode='HTML', reply_markup=markup)
        except Exception:
            bot.send_message(call.message.chat.id, f"✅ Stopped: {file_name}")
        log_action(user_id, "SCRIPT_STOP", f"Stopped {file_name}")

def delete_user_file(call, file_name):
    user_id = call.from_user.id
    if is_bot_running(user_id, file_name):
        bot.answer_callback_query(call.id, "⚠️ Stop script first!")
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Yes, Delete", callback_data=f"confirm_delete_{file_name}"),
        types.InlineKeyboardButton("❌ No", callback_data=f"cancel_delete_{file_name}"))
    try:
        bot.edit_message_text(
            f"⚠️ <b>Delete?</b>\n<code>{file_name}</code>\nThis cannot be undone!",
            call.message.chat.id, call.message.message_id,
            parse_mode='HTML', reply_markup=markup)
    except Exception:
        pass
    bot.answer_callback_query(call.id)

def confirm_delete_file(call, file_name):
    user_id = call.from_user.id
    file_path = os.path.join(get_user_folder(user_id), file_name)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        with data_lock:
            if user_id in user_files:
                user_files[user_id] = [(n, t) for n, t in user_files[user_id] if n != file_name]
        remove_user_file_db(user_id, file_name)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📂 Back to Files", callback_data="back_to_files"))
        try:
            bot.edit_message_text(
                f"✅ <b>Deleted:</b> <code>{file_name}</code>",
                call.message.chat.id, call.message.message_id,
                parse_mode='HTML', reply_markup=markup)
        except Exception:
            bot.send_message(call.message.chat.id, f"✅ Deleted: {file_name}")
        bot.answer_callback_query(call.id, "✅ Deleted!")
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Error: {str(e)[:30]}")

def download_user_file(call, file_name):
    user_id = call.from_user.id
    file_path = os.path.join(get_user_folder(user_id), file_name)
    if not os.path.exists(file_path):
        bot.answer_callback_query(call.id, "❌ File not found!")
        return
    bot.answer_callback_query(call.id, "📥 Sending...")
    try:
        with open(file_path, 'rb') as f:
            bot.send_document(call.message.chat.id, f, caption=f"📄 {file_name}")
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Error: {str(e)[:100]}")

def show_script_logs(call, file_name):
    user_id = call.from_user.id
    script_key = f"{user_id}_{file_name}"
    log_path = os.path.join(LOGS_DIR, f"{script_key}.log")
    if not os.path.exists(log_path):
        bot.answer_callback_query(call.id, "📋 No logs")
        return
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            logs = f.read()[-2000:] or "No output yet..."
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("🔄 Refresh", callback_data=f"logs_{file_name}"),
            types.InlineKeyboardButton("🔙 Back", callback_data=f"file_{file_name}"))
        try:
            bot.edit_message_text(
                f"📋 <b>Logs: {file_name}</b>\n<code>{logs[:1500]}</code>",
                call.message.chat.id, call.message.message_id,
                parse_mode='HTML', reply_markup=markup)
        except telebot.apihelper.ApiTelegramException:
            bot.answer_callback_query(call.id, "📋 Logs unchanged")
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Error: {str(e)[:30]}")

def restart_user_script(call, file_name):
    user_id = call.from_user.id
    script_key = f"{user_id}_{file_name}"
    if script_key in bot_scripts:
        kill_process_tree(bot_scripts[script_key])
        cleanup_script(script_key)
        time.sleep(0.5)
    run_user_script(call, file_name)

def show_user_files_callback(call):
    class FakeMsg:
        def __init__(self, c):
            self.chat = c.message.chat
            self.from_user = c.from_user
    show_user_files(FakeMsg(call))
    bot.answer_callback_query(call.id)

def stop_all_bots(call):
    if call.from_user.id != OWNER_ID and call.from_user.id not in admin_ids:
        bot.answer_callback_query(call.id, "❌ Admin only!")
        return
    bot.answer_callback_query(call.id, "🛑 Stopping all...")
    stopped = 0
    for sk in list(bot_scripts.keys()):
        try:
            kill_process_tree(bot_scripts[sk])
            cleanup_script(sk)
            stopped += 1
        except Exception:
            pass
    bot.send_message(call.message.chat.id, f"✅ Stopped {stopped} bot(s).")

def refresh_admin_panel(call):
    if call.from_user.id != OWNER_ID and call.from_user.id not in admin_ids:
        bot.answer_callback_query(call.id, "❌ Admin only!")
        return
    class FakeMsg:
        def __init__(self, c):
            self.chat = c.message.chat
            self.from_user = c.from_user
    show_admin_panel(FakeMsg(call))
    bot.answer_callback_query(call.id, "🔄 Refreshed!")

def show_admin_logs(call):
    if call.from_user.id != OWNER_ID and call.from_user.id not in admin_ids:
        bot.answer_callback_query(call.id, "❌ Admin only!")
        return
    bot.answer_callback_query(call.id)
    try:
        conn = get_db()
        rows = conn.execute(
            'SELECT user_id, action, details, timestamp FROM bot_logs ORDER BY id DESC LIMIT 20'
        ).fetchall()
        conn.close()
        if rows:
            text = "📋 <b>Recent Logs:</b>\n"
            for r in rows:
                text += f"👤 {r['user_id']} | {r['action']}\n{r['details'][:30]}\n🕐 {r['timestamp'][:16]}\n\n"
        else:
            text = "📋 No logs."
        bot.send_message(call.message.chat.id, text[:4000], parse_mode='HTML')
    except Exception as e:
        logger.error(f"show_admin_logs: {e}")


# ============================================================
# 🧹 CLEANUP ON EXIT
# ============================================================

def cleanup_on_exit():
    logger.info("Cleaning up AMMAR DEVX...")
    for sk in list(bot_scripts.keys()):
        try:
            kill_process_tree(bot_scripts[sk])
        except Exception:
            pass
    logger.info("Cleanup complete.")

atexit.register(cleanup_on_exit)


# ============================================================
# 🚀 MAIN
# ============================================================

def main():
    logger.info("=" * 50)
    logger.info("🤖 Starting AMMAR DEVX 🦁 Bot...")
    logger.info(f"📁 Base Dir: {BASE_DIR}")
    logger.info(f"💾 Database: {DATABASE_PATH}")
    logger.info("=" * 50)

    keep_alive()
    start_daily_report_scheduler()   # ✅ Daily report
    start_script_watchdog()          # ✅ Crash detection & runtime limit

    while True:
        try:
            logger.info("🚀 Starting bot polling...")
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except requests.exceptions.ConnectionError:
            logger.error("Connection error! Retrying in 10s...")
            time.sleep(10)
        except requests.exceptions.ReadTimeout:
            logger.error("Read timeout! Retrying in 5s...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Bot error: {e}", exc_info=True)
            time.sleep(5)

if __name__ == "__main__":
    main()
