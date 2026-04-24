# -*- coding: utf-8 -*-
# ============================================================
#   Dark Shadow 🖤 - Ultimate Bot Hosting
#   Features: User Mgmt, Bot Control, Analytics, Payment,
#             Notifications, Security, Web Dashboard,
#             Script Editor, Templates, Backup, Scheduler,
#             Auto Restart, Usage Stats
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
import schedule
import io
import base64
from collections import defaultdict
from functools import wraps

# --- Flask Web Dashboard + Keep Alive ---
from flask import Flask, render_template_string, jsonify, request, redirect, url_for, session
from threading import Thread

app = Flask(__name__)
app.secret_key = os.environ.get('DASHBOARD_SECRET', 'darkshadow_secret_2024')
DASHBOARD_PASSWORD = os.environ.get('DASHBOARD_PASS', 'darkshadow2024')

# ── Web Dashboard HTML ────────────────────────────────────────
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🦁 Dark Shadow Dashboard</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:'Segoe UI',sans-serif; background:#0f0f1a; color:#e0e0e0; }
  .navbar { background:#1a1a2e; padding:15px 30px; display:flex; justify-content:space-between; align-items:center; border-bottom:2px solid #7c3aed; }
  .navbar h1 { color:#7c3aed; font-size:1.4rem; }
  .navbar a { color:#aaa; text-decoration:none; font-size:0.9rem; }
  .container { padding:25px; max-width:1200px; margin:auto; }
  .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:20px; margin-bottom:25px; }
  .card { background:#1a1a2e; border-radius:12px; padding:20px; border:1px solid #2d2d4e; }
  .card h3 { color:#7c3aed; margin-bottom:8px; font-size:0.9rem; text-transform:uppercase; }
  .card .value { font-size:2rem; font-weight:bold; color:#fff; }
  .card .sub { font-size:0.8rem; color:#888; margin-top:4px; }
  .section { background:#1a1a2e; border-radius:12px; padding:20px; margin-bottom:20px; border:1px solid #2d2d4e; }
  .section h2 { color:#7c3aed; margin-bottom:15px; font-size:1rem; }
  table { width:100%; border-collapse:collapse; font-size:0.85rem; }
  th { color:#7c3aed; text-align:left; padding:8px; border-bottom:1px solid #2d2d4e; }
  td { padding:8px; border-bottom:1px solid #1a1a2e; color:#ccc; }
  tr:hover td { background:#16213e; }
  .badge { padding:3px 10px; border-radius:20px; font-size:0.75rem; font-weight:bold; }
  .badge.green { background:#065f46; color:#34d399; }
  .badge.red { background:#7f1d1d; color:#f87171; }
  .badge.purple { background:#4c1d95; color:#a78bfa; }
  .badge.yellow { background:#78350f; color:#fbbf24; }
  .progress-bar { background:#2d2d4e; border-radius:10px; height:8px; margin-top:5px; }
  .progress-fill { background:#7c3aed; border-radius:10px; height:8px; }
  .stat-row { display:flex; justify-content:space-between; margin:6px 0; font-size:0.85rem; }
  .btn { background:#7c3aed; color:#fff; border:none; padding:6px 14px; border-radius:8px; cursor:pointer; font-size:0.8rem; }
  .btn:hover { background:#6d28d9; }
  .btn.red { background:#dc2626; }
  .btn.red:hover { background:#b91c1c; }
  .login-box { max-width:360px; margin:100px auto; background:#1a1a2e; border-radius:16px; padding:36px; border:1px solid #7c3aed; text-align:center; }
  .login-box h2 { color:#7c3aed; margin-bottom:24px; }
  .login-box input { width:100%; padding:10px 14px; background:#0f0f1a; border:1px solid #2d2d4e; border-radius:8px; color:#fff; margin-bottom:14px; font-size:1rem; }
  .login-box button { width:100%; padding:10px; background:#7c3aed; color:#fff; border:none; border-radius:8px; font-size:1rem; cursor:pointer; }
  .alert { background:#1e3a5f; border-left:4px solid #3b82f6; padding:10px 14px; border-radius:6px; margin-bottom:14px; font-size:0.85rem; }
  @media(max-width:600px){ .grid{grid-template-columns:1fr 1fr;} }
</style>
</head>
<body>
{% if not logged_in %}
<div class="login-box">
  <h2>🦁 Dark Shadow</h2>
  <p style="color:#888;margin-bottom:20px;font-size:0.85rem;">Dashboard Login</p>
  {% if error %}<div class="alert" style="background:#3b1c1c;border-color:#ef4444;">{{ error }}</div>{% endif %}
  <form method="POST" action="/login">
    <input type="password" name="password" placeholder="Enter password..." autofocus>
    <button type="submit">Login →</button>
  </form>
</div>
{% else %}
<div class="navbar">
  <h1>🦁 Dark Shadow Dashboard</h1>
  <div style="display:flex;gap:20px;align-items:center;">
    <span style="color:#34d399;font-size:0.85rem;">● Live</span>
    <a href="/logout">Logout</a>
  </div>
</div>
<div class="container">
  <!-- Stats Cards -->
  <div class="grid">
    <div class="card">
      <h3>👥 Total Users</h3>
      <div class="value">{{ stats.users }}</div>
      <div class="sub">{{ stats.active_today }} active today</div>
    </div>
    <div class="card">
      <h3>🤖 Running Bots</h3>
      <div class="value" style="color:#34d399;">{{ stats.running }}</div>
      <div class="sub">out of {{ stats.total_scripts }} scripts</div>
    </div>
    <div class="card">
      <h3>💳 Subscriptions</h3>
      <div class="value" style="color:#a78bfa;">{{ stats.active_subs }}</div>
      <div class="sub">{{ stats.pending_pay }} pending payments</div>
    </div>
    <div class="card">
      <h3>🚫 Banned</h3>
      <div class="value" style="color:#f87171;">{{ stats.banned }}</div>
      <div class="sub">{{ stats.warnings }} total warnings</div>
    </div>
    <div class="card">
      <h3>💻 CPU</h3>
      <div class="value">{{ stats.cpu }}%</div>
      <div class="progress-bar"><div class="progress-fill" style="width:{{ stats.cpu }}%"></div></div>
    </div>
    <div class="card">
      <h3>🧠 RAM</h3>
      <div class="value">{{ stats.ram }}%</div>
      <div class="progress-bar"><div class="progress-fill" style="width:{{ stats.ram }}%"></div></div>
    </div>
    <div class="card">
      <h3>💾 Disk</h3>
      <div class="value">{{ stats.disk }}%</div>
      <div class="progress-bar"><div class="progress-fill" style="width:{{ stats.disk }}%"></div></div>
    </div>
    <div class="card">
      <h3>⏱️ Uptime</h3>
      <div class="value" style="font-size:1.2rem;margin-top:8px;">{{ stats.uptime }}</div>
      <div class="sub">Bot running since start</div>
    </div>
  </div>

  <!-- Running Bots -->
  <div class="section">
    <h2>🟢 Running Bots</h2>
    {% if running_bots %}
    <table>
      <tr><th>File</th><th>User ID</th><th>PID</th><th>Runtime</th><th>Action</th></tr>
      {% for b in running_bots %}
      <tr>
        <td>{{ b.file }}</td>
        <td>{{ b.user_id }}</td>
        <td><span class="badge green">{{ b.pid }}</span></td>
        <td>{{ b.runtime }}</td>
        <td><form method="POST" action="/stop_bot" style="display:inline">
          <input type="hidden" name="key" value="{{ b.key }}">
          <button class="btn red" type="submit">Stop</button>
        </form></td>
      </tr>
      {% endfor %}
    </table>
    {% else %}
    <p style="color:#666;font-size:0.85rem;">No bots running currently.</p>
    {% endif %}
  </div>

  <!-- Recent Users -->
  <div class="section">
    <h2>👥 Recent Users</h2>
    <table>
      <tr><th>User ID</th><th>Username</th><th>Status</th><th>Files</th><th>Last Seen</th></tr>
      {% for u in recent_users %}
      <tr>
        <td>{{ u.user_id }}</td>
        <td>@{{ u.username or "N/A" }}</td>
        <td>
          {% if u.is_banned %}<span class="badge red">Banned</span>
          {% elif u.is_admin %}<span class="badge purple">Admin</span>
          {% elif u.has_sub %}<span class="badge yellow">Premium</span>
          {% else %}<span class="badge green">Free</span>{% endif %}
        </td>
        <td>{{ u.file_count }}</td>
        <td>{{ u.last_seen[:16] if u.last_seen else "N/A" }}</td>
      </tr>
      {% endfor %}
    </table>
  </div>

  <!-- Analytics -->
  <div class="section">
    <h2>📊 Today's Analytics</h2>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:14px;">
      {% for key, val in analytics.items() %}
      <div style="background:#0f0f1a;padding:12px;border-radius:8px;text-align:center;">
        <div style="color:#7c3aed;font-size:0.75rem;text-transform:uppercase;">{{ key }}</div>
        <div style="font-size:1.4rem;font-weight:bold;margin-top:4px;">{{ val }}</div>
      </div>
      {% endfor %}
    </div>
  </div>

  <!-- Scheduled Jobs -->
  <div class="section">
    <h2>⏰ Scheduled Jobs</h2>
    {% if scheduled_jobs %}
    <table>
      <tr><th>User</th><th>File</th><th>Run At</th><th>Status</th></tr>
      {% for j in scheduled_jobs %}
      <tr>
        <td>{{ j.user_id }}</td>
        <td>{{ j.file_name }}</td>
        <td>{{ j.run_at }}</td>
        <td><span class="badge {{ 'green' if j.active else 'red' }}">{{ 'Active' if j.active else 'Done' }}</span></td>
      </tr>
      {% endfor %}
    </table>
    {% else %}
    <p style="color:#666;font-size:0.85rem;">No scheduled jobs.</p>
    {% endif %}
  </div>

  <p style="text-align:center;color:#444;font-size:0.75rem;margin-top:20px;">
    🦁 Dark Shadow Dashboard • Auto-refresh every 30s
  </p>
</div>
<script>setTimeout(()=>location.reload(), 30000);</script>
{% endif %}
</body>
</html>
'''

# ── Flask Routes ──────────────────────────────────────────────

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template_string(DASHBOARD_HTML, logged_in=False, error=None)
    return redirect('/dashboard')

@app.route('/login', methods=['POST'])
def login():
    pwd = request.form.get('password','')
    if pwd == DASHBOARD_PASSWORD:
        session['logged_in'] = True
        return redirect('/dashboard')
    return render_template_string(DASHBOARD_HTML, logged_in=False, error='❌ Wrong password!')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect('/')
    # Stats
    running_list = []
    for sk, info in list(bot_scripts.items()):
        if is_bot_running_check(sk):
            rt = str(datetime.now() - info.get('start_time', datetime.now())).split('.')[0]
            running_list.append({
                'key': sk, 'file': info.get('file_name','?'),
                'user_id': info.get('user_id','?'),
                'pid': info['process'].pid if info.get('process') else 'N/A',
                'runtime': rt
            })
    # Recent users from DB
    conn = get_db()
    users_rows = conn.execute(
        'SELECT user_id, username, last_seen FROM active_users ORDER BY last_seen DESC LIMIT 20'
    ).fetchall()
    conn.close()
    recent_users = []
    for u in users_rows:
        fc = len(user_files.get(u['user_id'], []))
        recent_users.append({
            'user_id': u['user_id'],
            'username': u['username'],
            'last_seen': u['last_seen'] or '',
            'is_banned': u['user_id'] in banned_users,
            'is_admin': u['user_id'] in admin_ids,
            'has_sub': u['user_id'] in user_subscriptions and user_subscriptions[u['user_id']]['expiry'] > datetime.now(),
            'file_count': fc,
        })
    # Scheduled jobs
    sched_jobs = []
    conn2 = get_db()
    sj = conn2.execute('SELECT * FROM scheduled_jobs ORDER BY run_at DESC LIMIT 10').fetchall()
    conn2.close()
    for j in sj:
        sched_jobs.append({'user_id': j['user_id'], 'file_name': j['file_name'],
                           'run_at': j['run_at'], 'active': j['active']})

    stats = {
        'users': len(active_users),
        'active_today': len(analytics['daily_active']),
        'running': len(running_list),
        'total_scripts': sum(len(v) for v in user_files.values()),
        'active_subs': len([u for u,d in user_subscriptions.items() if d['expiry'] > datetime.now()]),
        'pending_pay': len(pending_payments),
        'banned': len(banned_users),
        'warnings': sum(user_warnings.values()),
        'cpu': psutil.cpu_percent(interval=0.5),
        'ram': psutil.virtual_memory().percent,
        'disk': psutil.disk_usage('/').percent,
        'uptime': get_uptime(),
    }
    analytics_display = {
        'Commands': sum(analytics['commands_today'].values()),
        'Uploads': analytics['uploads_today'],
        'Scripts Run': analytics['scripts_run_today'],
        'Errors': analytics['errors_today'],
        'Active Users': len(analytics['daily_active']),
    }
    return render_template_string(DASHBOARD_HTML, logged_in=True,
        stats=stats, running_bots=running_list,
        recent_users=recent_users, analytics=analytics_display,
        scheduled_jobs=sched_jobs)

@app.route('/stop_bot', methods=['POST'])
def stop_bot_web():
    if not session.get('logged_in'):
        return redirect('/')
    key = request.form.get('key','')
    if key in bot_scripts:
        kill_process_tree(bot_scripts[key])
        cleanup_script(key)
    return redirect('/dashboard')

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "uptime": get_uptime(),
                    "running_bots": len(bot_scripts), "users": len(active_users)})

@app.route('/api/stats')
def api_stats():
    return jsonify({
        "cpu": psutil.cpu_percent(),
        "ram": psutil.virtual_memory().percent,
        "running_bots": len([k for k in bot_scripts if is_bot_running_check(k)]),
        "users": len(active_users),
        "uptime": get_uptime()
    })

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    print("✅ Flask Dashboard + Keep-Alive started.")

# --- Configuration (Use environment variables!) ---
TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_TOKEN_HERE')  # ⚠️ Set in environment!
OWNER_ID = int(os.environ.get('OWNER_ID', '7847937078'))
ADMIN_ID = int(os.environ.get('ADMIN_ID', '7847937078'))
YOUR_USERNAME = os.environ.get('YOUR_USERNAME', '@DarkShadow')
UPDATE_CHANNEL = os.environ.get('UPDATE_CHANNEL', 'https://t.me/DarkConflig')

# Folder setup
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_BOTS_DIR = os.path.join(BASE_DIR, 'upload_bots')
DS_DIR = os.path.join(BASE_DIR, 'ds_data')
DATABASE_PATH = os.path.join(DS_DIR, 'bot_data.db')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# File upload limits
FREE_USER_LIMIT = 10
SUBSCRIBED_USER_LIMIT = 15
ADMIN_LIMIT = 999
OWNER_LIMIT = float('ds_data')

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

# ✅ NEW: Extra directories
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')
MAX_BACKUPS_PER_USER = 5

# Create directories
os.makedirs(UPLOAD_BOTS_DIR, exist_ok=True)
os.makedirs(DS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

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

# ✅ NEW: Auto-restart tracking
auto_restart_enabled = {}    # script_key -> bool
restart_counts = defaultdict(int)  # script_key -> count
MAX_RESTARTS = 5

# ✅ NEW: Script editor
pending_edits = {}  # user_id -> {'file': ..., 'content': ...}

# ✅ NEW: Usage stats per user
user_usage_stats = defaultdict(lambda: {
    'commands': 0, 'uploads': 0, 'scripts_run': 0,
    'last_active': None, 'total_runtime_mins': 0
})

# ✅ NEW: Scheduled jobs (in-memory)
scheduled_jobs_memory = {}  # job_id -> info

# ✅ NEW: Bot Templates
BOT_TEMPLATES = {
    'echo': {
        'name': '🔁 Echo Bot', 'desc': 'Jo bhejo wahi wapas aata hai',
        'file': 'echo_bot.py',
        'code': 'import telebot, os\nbot = telebot.TeleBot(os.environ.get("BOT_TOKEN","YOUR_TOKEN"))\n\n@bot.message_handler(func=lambda m: True)\ndef echo(m): bot.reply_to(m, m.text)\n\nprint("Echo Bot running!")\nbot.infinity_polling()\n'
    },
    'welcome': {
        'name': '👋 Welcome Bot', 'desc': 'Naye members ko welcome karta hai',
        'file': 'welcome_bot.py',
        'code': 'import telebot, os\nbot = telebot.TeleBot(os.environ.get("BOT_TOKEN","YOUR_TOKEN"))\n\n@bot.message_handler(content_types=["new_chat_members"])\ndef welcome(message):\n    for m in message.new_chat_members:\n        bot.send_message(message.chat.id, f"👋 Welcome {m.first_name}!")\n\n@bot.message_handler(commands=["start"])\ndef start(m): bot.reply_to(m, "👋 Welcome Bot ready!")\n\nbot.infinity_polling()\n'
    },
    'calculator': {
        'name': '🔢 Calculator Bot', 'desc': 'Basic math calculator',
        'file': 'calculator_bot.py',
        'code': 'import telebot, os\nbot = telebot.TeleBot(os.environ.get("BOT_TOKEN","YOUR_TOKEN"))\n\n@bot.message_handler(commands=["calc"])\ndef calc(message):\n    try:\n        expr = message.text.replace("/calc","").strip()\n        allowed = set("0123456789+-*/(). ")\n        if all(c in allowed for c in expr):\n            bot.reply_to(message, f"✅ {expr} = {eval(expr)}")\n        else:\n            bot.reply_to(message, "❌ Invalid!")\n    except Exception as e:\n        bot.reply_to(message, f"❌ {e}")\n\n@bot.message_handler(commands=["start"])\ndef start(m): bot.reply_to(m, "🔢 Use /calc 5+3")\n\nbot.infinity_polling()\n'
    },
    'poll': {
        'name': '📊 Poll Bot', 'desc': 'Group mein polls banata hai',
        'file': 'poll_bot.py',
        'code': 'import telebot, os\nbot = telebot.TeleBot(os.environ.get("BOT_TOKEN","YOUR_TOKEN"))\n\n@bot.message_handler(commands=["poll"])\ndef poll(message):\n    try:\n        text = message.text.replace("/poll","").strip()\n        q, opts_str = text.split("?")\n        opts = [o.strip() for o in opts_str.split("|")]\n        bot.send_poll(message.chat.id, q.strip()+"?", opts)\n    except:\n        bot.reply_to(message, "Format: /poll Sawaal? Opt1 | Opt2")\n\n@bot.message_handler(commands=["start"])\ndef start(m): bot.reply_to(m, "📊 Use /poll Q? A | B | C")\n\nbot.infinity_polling()\n'
    },
    'reminder': {
        'name': '⏰ Reminder Bot', 'desc': 'Reminders set karne wala bot',
        'file': 'reminder_bot.py',
        'code': 'import telebot, os, time, threading\nbot = telebot.TeleBot(os.environ.get("BOT_TOKEN","YOUR_TOKEN"))\n\n@bot.message_handler(commands=["remind"])\ndef remind(message):\n    try:\n        parts = message.text.split(maxsplit=2)\n        mins = int(parts[1]); text = parts[2] if len(parts)>2 else "Reminder!"\n        chat_id = message.chat.id\n        bot.reply_to(message, f"✅ {mins} min baad remind karunga!")\n        def send():\n            time.sleep(mins*60)\n            bot.send_message(chat_id, f"⏰ REMINDER: {text}")\n        threading.Thread(target=send, daemon=True).start()\n    except Exception as e:\n        bot.reply_to(message, f"❌ /remind 10 Namaz ka waqt")\n\n@bot.message_handler(commands=["start"])\ndef start(m): bot.reply_to(m, "⏰ Use /remind 10 Namaz")\n\nbot.infinity_polling()\n'
    },
}

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
║     📊 <b>Dark Shadow ANALYTICS</b> 📊      ║
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
                        # ✅ AUTO RESTART
                        if auto_restart_enabled.get(script_key, False):
                            if restart_counts[script_key] < MAX_RESTARTS:
                                restart_counts[script_key] += 1
                                count = restart_counts[script_key]
                                logger.info(f"Auto-restarting {script_key} (attempt {count})")
                                try:
                                    bot.send_message(info['user_id'],
                                        f"🔄 <b>Auto Restart #{count}</b>\n"
                                        f"📄 <code>{info['file_name']}</code> crashed — restarting...")
                                except Exception:
                                    pass
                                # Re-run in new thread
                                sp = info.get('script_path','')
                                uid = info.get('user_id')
                                fn  = info.get('file_name','')
                                stype = info.get('type','py')
                                folder = get_user_folder(uid)
                                cleanup_script(script_key)
                                class FakeMsgRestart:
                                    class chat:
                                        id = uid
                                if sp and os.path.exists(sp):
                                    threading.Thread(
                                        target=run_script_generic,
                                        args=(sp, uid, folder, fn, FakeMsgRestart(), stype),
                                        daemon=True).start()
                            else:
                                logger.warning(f"Max restarts reached for {script_key}")
                                try:
                                    bot.send_message(info['user_id'],
                                        f"❌ <b>Auto Restart Failed</b>\n"
                                        f"📄 <code>{info['file_name']}</code>\n"
                                        f"Reached max {MAX_RESTARTS} restarts. Check your code!")
                                except Exception:
                                    pass
                                auto_restart_enabled[script_key] = False
                                notify_crash(script_key, info['file_name'], info['user_id'], error_snippet)
                                cleanup_script(script_key)
                        else:
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
║       📊 <b>Dark Shadow STATS</b> 📊         ║
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
            CREATE TABLE IF NOT EXISTS scheduled_jobs
                (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                 file_name TEXT, run_at TEXT, repeat TEXT, active INTEGER DEFAULT 1,
                 created_at TEXT);
            CREATE TABLE IF NOT EXISTS backups
                (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                 file_name TEXT, backup_path TEXT, created_at TEXT);
            CREATE TABLE IF NOT EXISTS usage_stats
                (user_id INTEGER PRIMARY KEY, commands INTEGER DEFAULT 0,
                 uploads INTEGER DEFAULT 0, scripts_run INTEGER DEFAULT 0,
                 total_runtime_mins INTEGER DEFAULT 0, last_active TEXT);
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
            f"║      🚀 <b>Dark Shadow: STARTING</b> 🚀       ║\n"
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
                f"║     ✅ <b>Dark Shadow: RUNNING</b> ✅        ║\n"
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
                f"║     ❌ <b>Dark Shadow: FAILED</b> ❌         ║\n"
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
    limit_str = str(int(limit)) if limit != float('ds_data') else '∞'
    welcome = (
        f"╔══════════════════════════════════════╗\n"
        f"║    🤖 <b>Dark Shadow 🖤</b>                 ║\n"
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
        "║       📚 <b>Dark Shadow HELP</b> 📚          ║\n"
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
        f"║        ⚡ <b>Dark Shadow SPEED</b> ⚡        ║\n"
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
    limit_str = str(int(limit)) if limit != float('ds_data') else '∞'
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
        "║     💰 <b>Dark Shadow PLANS</b> 💰          ║\n"
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
    limit_str = str(int(limit)) if limit != float('ds_data') else '∞'
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
                f"║      📢 <b>Dark Shadow BROADCAST</b> 📢    ║\n"
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
    limit_str = str(int(limit)) if limit != float('ds_data') else '∞'
    if count >= limit:
        bot.reply_to(message,
            f"❌ File limit reached! ({count}/{limit_str})\n"
            f"💰 Upgrade plan: /buy")
        return
    bot.send_message(message.chat.id,
        f"╔══════════════════════════════════════╗\n"
        f"║       📤 <b>Dark Shadow: UPLOAD</b> 📤      ║\n"
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
    limit_str = str(int(limit)) if limit != float('ds_data') else '∞'

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
        f"║      📤 <b>Dark Shadow: UPLOADING</b> 📤     ║\n"
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
# 📊 USAGE STATS COMMANDS
# ============================================================

@bot.message_handler(commands=['myusage'])
@security_check
def myusage_cmd(message):
    uid = message.from_user.id
    track_command('myusage', uid)
    s = user_usage_stats[uid]
    running = len([k for k,v in bot_scripts.items()
                   if v.get('user_id') == uid and is_bot_running_check(k)])
    text = (
        f"╔══════════════════════════════════════╗\n"
        f"║     📊 <b>YOUR USAGE STATS</b>             ║\n"
        f"╠══════════════════════════════════════╣\n"
        f"║  🆔 ID: <code>{uid}</code>\n"
        f"║  💬 Commands Used: {s['commands']}\n"
        f"║  📤 Files Uploaded: {s['uploads']}\n"
        f"║  🤖 Scripts Run: {s['scripts_run']}\n"
        f"║  ⏱️ Total Runtime: {s['total_runtime_mins']} mins\n"
        f"║  🟢 Currently Running: {running}\n"
        f"║  📁 Files Stored: {get_user_file_count(uid)}\n"
        f"║  🏷️ Status: {get_user_status_label(uid)}\n"
        f"╚══════════════════════════════════════╝"
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['allusage'])
def allusage_cmd(message):
    if message.from_user.id != OWNER_ID and message.from_user.id not in admin_ids:
        bot.reply_to(message, "❌ Admin only!")
        return
    track_command('allusage', message.from_user.id)
    if not user_usage_stats:
        bot.reply_to(message, "📊 No usage data yet.")
        return
    top = sorted(user_usage_stats.items(),
                 key=lambda x: x[1]['scripts_run'], reverse=True)[:10]
    text = "╔══════════════════════════════════════╗\n║    📊 <b>ALL USERS USAGE</b>               ║\n╠══════════════════════════════════════╣\n"
    for uid, s in top:
        text += (f"║ 👤 {uid}\n"
                 f"║   Cmds:{s['commands']} | Uploads:{s['uploads']} | Runs:{s['scripts_run']}\n")
    text += "╚══════════════════════════════════════╝"
    bot.send_message(message.chat.id, text, parse_mode='HTML')


# ============================================================
# 🔄 AUTO RESTART COMMANDS
# ============================================================

@bot.message_handler(commands=['autorestart'])
@security_check
def autorestart_cmd(message):
    uid = message.from_user.id
    track_command('autorestart', uid)
    files = user_files.get(uid, [])
    if not files:
        bot.reply_to(message, "❌ Koi file nahi! Pehle upload karo.")
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for fname, ftype in files:
        sk = f"{uid}_{fname}"
        status = "✅ ON" if auto_restart_enabled.get(sk, False) else "❌ OFF"
        markup.add(types.InlineKeyboardButton(
            f"{status} — {fname[:25]}",
            callback_data=f"ar_toggle_{fname}"))
    bot.send_message(message.chat.id,
        "🔄 <b>Auto Restart Settings</b>\nSelect script to toggle:",
        parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ar_toggle_"))
def ar_toggle_cb(call):
    uid = call.from_user.id
    fname = call.data[10:]
    sk = f"{uid}_{fname}"
    auto_restart_enabled[sk] = not auto_restart_enabled.get(sk, False)
    restart_counts[sk] = 0  # reset count
    status = "✅ ON" if auto_restart_enabled[sk] else "❌ OFF"
    bot.answer_callback_query(call.id, f"Auto Restart: {status}")
    bot.send_message(call.message.chat.id,
        f"🔄 <b>Auto Restart {status}</b>\n📄 <code>{fname}</code>\n"
        f"{'Bot crash hone pe automatically restart hoga!' if auto_restart_enabled[sk] else 'Auto restart band hai.'}",
        parse_mode='HTML')


# ============================================================
# 📝 SCRIPT EDITOR COMMANDS
# ============================================================

@bot.message_handler(commands=['edit'])
@security_check
def edit_cmd(message):
    uid = message.from_user.id
    track_command('edit', uid)
    files = user_files.get(uid, [])
    editable = [(n, t) for n, t in files if t in ('py','js','txt','json','yml','yaml')]
    if not editable:
        bot.reply_to(message, "❌ Koi editable file nahi!")
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for fname, ftype in editable:
        icon = "🐍" if ftype == "py" else "🟨" if ftype == "js" else "📄"
        markup.add(types.InlineKeyboardButton(
            f"{icon} {fname[:30]}", callback_data=f"edit_open_{fname}"))
    bot.send_message(message.chat.id,
        "📝 <b>Script Editor</b>\nKaunsi file edit karni hai?",
        parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("edit_open_"))
def edit_open_cb(call):
    uid = call.from_user.id
    fname = call.data[10:]
    fpath = os.path.join(get_user_folder(uid), fname)
    if not os.path.exists(fpath):
        bot.answer_callback_query(call.id, "❌ File nahi mili!")
        return
    try:
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        bot.answer_callback_query(call.id)
        # Show first 2000 chars as preview
        preview = content[:1500] if len(content) > 1500 else content
        bot.send_message(call.message.chat.id,
            f"📝 <b>Editing:</b> <code>{fname}</code>\n"
            f"📏 Size: {len(content)} chars\n\n"
            f"<b>Current Content (preview):</b>\n<code>{preview}</code>\n\n"
            f"➡️ Ab naya content bhejo (poora file replace ho jaayega):\n"
            f"⚠️ Cancel karne ke liye /cancel bhejo",
            parse_mode='HTML')
        pending_edits[uid] = {'file': fname, 'path': fpath}
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, process_edit)
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Error: {str(e)[:100]}")

def process_edit(message):
    uid = message.from_user.id
    if message.text and message.text.strip() == '/cancel':
        pending_edits.pop(uid, None)
        bot.reply_to(message, "❌ Edit cancelled.")
        return
    if uid not in pending_edits:
        return
    edit_info = pending_edits.pop(uid)
    fname = edit_info['file']
    fpath = edit_info['path']
    new_content = message.text or ""
    if not new_content.strip():
        bot.reply_to(message, "❌ Empty content! Edit cancelled.")
        return
    try:
        # Auto backup before edit
        create_backup(uid, fname)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("▶️ Run Now", callback_data=f"run_{fname}"),
            types.InlineKeyboardButton("📂 Files", callback_data="back_to_files"))
        bot.reply_to(message,
            f"✅ <b>File Updated!</b>\n"
            f"📄 <code>{fname}</code>\n"
            f"📏 {len(new_content)} chars saved\n"
            f"💾 Auto backup bana diya!",
            parse_mode='HTML', reply_markup=markup)
        log_action(uid, "SCRIPT_EDIT", f"Edited {fname}")
    except Exception as e:
        bot.reply_to(message, f"❌ Save failed: {str(e)[:100]}")


# ============================================================
# 💾 BACKUP SYSTEM
# ============================================================

def create_backup(user_id, file_name):
    """Automatic file backup banana"""
    try:
        src = os.path.join(get_user_folder(user_id), file_name)
        if not os.path.exists(src):
            return False
        user_backup_dir = os.path.join(BACKUP_DIR, str(user_id))
        os.makedirs(user_backup_dir, exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{file_name}_{ts}.bak"
        dst = os.path.join(user_backup_dir, backup_name)
        shutil.copy2(src, dst)
        # Save to DB
        conn = get_db()
        conn.execute(
            'INSERT INTO backups (user_id, file_name, backup_path, created_at) VALUES (?,?,?,?)',
            (user_id, file_name, dst, datetime.now().isoformat()))
        conn.commit()
        # Keep only MAX_BACKUPS_PER_USER per file
        rows = conn.execute(
            'SELECT id, backup_path FROM backups WHERE user_id=? AND file_name=? ORDER BY id DESC',
            (user_id, file_name)).fetchall()
        if len(rows) > MAX_BACKUPS_PER_USER:
            for row in rows[MAX_BACKUPS_PER_USER:]:
                try:
                    os.remove(row['backup_path'])
                except Exception:
                    pass
                conn.execute('DELETE FROM backups WHERE id=?', (row['id'],))
        conn.commit()
        conn.close()
        logger.info(f"Backup created: {backup_name}")
        return backup_name
    except Exception as e:
        logger.error(f"create_backup error: {e}")
        return False

@bot.message_handler(commands=['backup'])
@security_check
def backup_cmd(message):
    uid = message.from_user.id
    track_command('backup', uid)
    files = user_files.get(uid, [])
    if not files:
        bot.reply_to(message, "❌ Koi file nahi!")
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("📦 Backup ALL Files", callback_data="backup_all"))
    for fname, _ in files:
        markup.add(types.InlineKeyboardButton(
            f"💾 {fname[:30]}", callback_data=f"backup_one_{fname}"))
    bot.send_message(message.chat.id,
        "💾 <b>Backup System</b>\nKaunsi file ka backup lena hai?",
        parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "backup_all")
def backup_all_cb(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id, "⏳ Creating backups...")
    files = user_files.get(uid, [])
    ok = fail = 0
    for fname, _ in files:
        result = create_backup(uid, fname)
        if result:
            ok += 1
        else:
            fail += 1
    bot.send_message(call.message.chat.id,
        f"✅ <b>Backup Complete!</b>\n"
        f"✅ Success: {ok}\n❌ Failed: {fail}\n"
        f"💾 Max {MAX_BACKUPS_PER_USER} backups per file kept.",
        parse_mode='HTML')

@bot.callback_query_handler(func=lambda c: c.data.startswith("backup_one_"))
def backup_one_cb(call):
    uid = call.from_user.id
    fname = call.data[11:]
    bot.answer_callback_query(call.id, "⏳ Creating backup...")
    result = create_backup(uid, fname)
    if result:
        bot.send_message(call.message.chat.id,
            f"✅ <b>Backup Created!</b>\n📄 <code>{fname}</code>\n💾 <code>{result}</code>",
            parse_mode='HTML')
    else:
        bot.send_message(call.message.chat.id, "❌ Backup failed!")

@bot.message_handler(commands=['mybackups'])
@security_check
def mybackups_cmd(message):
    uid = message.from_user.id
    track_command('mybackups', uid)
    conn = get_db()
    rows = conn.execute(
        'SELECT file_name, backup_path, created_at FROM backups WHERE user_id=? ORDER BY id DESC LIMIT 20',
        (uid,)).fetchall()
    conn.close()
    if not rows:
        bot.reply_to(message, "💾 Koi backup nahi hai abhi.\nUse /backup to create one.")
        return
    text = "╔══════════════════════════════════════╗\n║       💾 <b>YOUR BACKUPS</b>               ║\n╠══════════════════════════════════════╣\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    for r in rows:
        ts = r['created_at'][:16] if r['created_at'] else "?"
        text += f"║ 📄 {r['file_name'][:20]} — {ts}\n"
        bname = os.path.basename(r['backup_path'])
        markup.add(types.InlineKeyboardButton(
            f"📥 {bname[:30]}", callback_data=f"restore_{bname}"))
    text += "╚══════════════════════════════════════╝\nClick to restore:"
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("restore_"))
def restore_backup_cb(call):
    uid = call.from_user.id
    bname = call.data[8:]
    conn = get_db()
    row = conn.execute('SELECT * FROM backups WHERE user_id=? AND backup_path LIKE ?',
                       (uid, f'%{bname}')).fetchone()
    conn.close()
    if not row:
        bot.answer_callback_query(call.id, "❌ Backup nahi mila!")
        return
    src = row['backup_path']
    fname = row['file_name']
    dst = os.path.join(get_user_folder(uid), fname)
    try:
        shutil.copy2(src, dst)
        bot.answer_callback_query(call.id, "✅ Restored!")
        bot.send_message(call.message.chat.id,
            f"✅ <b>Restored!</b>\n📄 <code>{fname}</code>\nFile purani state mein aa gayi!",
            parse_mode='HTML')
        log_action(uid, "BACKUP_RESTORE", f"Restored {fname} from {bname}")
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Restore failed!")
        bot.send_message(call.message.chat.id, f"❌ Restore error: {str(e)[:100]}")


# ============================================================
# ⏰ SCHEDULER COMMANDS
# ============================================================

def run_scheduler_loop():
    """Background thread: check scheduled jobs every minute"""
    while True:
        try:
            now = datetime.now()
            conn = get_db()
            jobs = conn.execute(
                "SELECT * FROM scheduled_jobs WHERE active=1"
            ).fetchall()
            conn.close()
            for job in jobs:
                try:
                    run_at = datetime.fromisoformat(job['run_at'])
                    if now >= run_at:
                        uid = job['user_id']
                        fname = job['file_name']
                        fpath = os.path.join(get_user_folder(uid), fname)
                        if os.path.exists(fpath):
                            class FakeMsgSched:
                                class chat:
                                    id = uid
                            stype = 'js' if fname.endswith('.js') else 'py'
                            threading.Thread(
                                target=run_script_generic,
                                args=(fpath, uid, get_user_folder(uid), fname,
                                      FakeMsgSched(), stype),
                                daemon=True).start()
                            try:
                                bot.send_message(uid,
                                    f"⏰ <b>Scheduled Run!</b>\n"
                                    f"📄 <code>{fname}</code> started automatically!")
                            except Exception:
                                pass
                        # Handle repeat or deactivate
                        conn2 = get_db()
                        repeat = job['repeat']
                        if repeat == 'daily':
                            next_run = (run_at + timedelta(days=1)).isoformat()
                            conn2.execute('UPDATE scheduled_jobs SET run_at=? WHERE id=?',
                                         (next_run, job['id']))
                        elif repeat == 'weekly':
                            next_run = (run_at + timedelta(weeks=1)).isoformat()
                            conn2.execute('UPDATE scheduled_jobs SET run_at=? WHERE id=?',
                                         (next_run, job['id']))
                        else:
                            conn2.execute('UPDATE scheduled_jobs SET active=0 WHERE id=?',
                                         (job['id'],))
                        conn2.commit()
                        conn2.close()
                except Exception as e:
                    logger.error(f"Scheduler job error: {e}")
        except Exception as e:
            logger.error(f"Scheduler loop error: {e}")
        time.sleep(60)

def start_scheduler():
    t = threading.Thread(target=run_scheduler_loop, daemon=True)
    t.start()
    logger.info("⏰ Scheduler started.")

@bot.message_handler(commands=['schedule'])
@security_check
def schedule_cmd(message):
    uid = message.from_user.id
    track_command('schedule', uid)
    files = user_files.get(uid, [])
    runnable = [(n, t) for n, t in files if t in ('py', 'js')]
    if not runnable:
        bot.reply_to(message, "❌ Koi Python/JS file nahi hai!")
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for fname, _ in runnable:
        markup.add(types.InlineKeyboardButton(
            f"⏰ {fname[:30]}", callback_data=f"sched_file_{fname}"))
    bot.send_message(message.chat.id,
        "⏰ <b>Scheduler</b>\nKaunsi file schedule karni hai?",
        parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("sched_file_"))
def sched_file_cb(call):
    fname = call.data[11:]
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🕐 1 min baad", callback_data=f"sched_set_{fname}_1min_once"),
        types.InlineKeyboardButton("🕐 1 ghante baad", callback_data=f"sched_set_{fname}_1hour_once"))
    markup.add(
        types.InlineKeyboardButton("🔁 Har roz", callback_data=f"sched_set_{fname}_1day_daily"),
        types.InlineKeyboardButton("🔁 Har hafte", callback_data=f"sched_set_{fname}_1week_weekly"))
    markup.add(types.InlineKeyboardButton("⌨️ Custom time", callback_data=f"sched_custom_{fname}"))
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id,
        f"⏰ <b>{fname}</b> kab run karna hai?",
        parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("sched_set_"))
def sched_set_cb(call):
    uid = call.from_user.id
    parts = call.data[10:].rsplit('_', 2)
    fname = parts[0]
    duration_str = parts[1]
    repeat = parts[2]
    duration_map = {'1min': timedelta(minutes=1), '1hour': timedelta(hours=1),
                    '1day': timedelta(days=1), '1week': timedelta(weeks=1)}
    delta = duration_map.get(duration_str, timedelta(hours=1))
    run_at = (datetime.now() + delta).isoformat()
    conn = get_db()
    conn.execute(
        'INSERT INTO scheduled_jobs (user_id, file_name, run_at, repeat, active, created_at) VALUES (?,?,?,?,1,?)',
        (uid, fname, run_at, repeat, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    repeat_label = {'once': 'Ek baar', 'daily': 'Har roz', 'weekly': 'Har hafte'}.get(repeat, repeat)
    bot.answer_callback_query(call.id, "✅ Scheduled!")
    bot.send_message(call.message.chat.id,
        f"✅ <b>Scheduled!</b>\n"
        f"📄 <code>{fname}</code>\n"
        f"⏰ Run at: {run_at[:16]}\n"
        f"🔁 Repeat: {repeat_label}\n"
        f"Use /myschedules to view all.",
        parse_mode='HTML')

@bot.callback_query_handler(func=lambda c: c.data.startswith("sched_custom_"))
def sched_custom_cb(call):
    fname = call.data[13:]
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id,
        f"⌨️ <b>Custom Schedule</b>\n"
        f"File: <code>{fname}</code>\n\n"
        f"Format mein bhejo:\n<code>YYYY-MM-DD HH:MM once</code>\n"
        f"Ya: <code>YYYY-MM-DD HH:MM daily</code>\n"
        f"Example: <code>2025-01-15 08:00 daily</code>",
        parse_mode='HTML')
    bot.register_next_step_handler(msg, process_custom_schedule, fname=fname)

def process_custom_schedule(message, fname):
    uid = message.from_user.id
    try:
        parts = message.text.strip().split()
        dt_str = f"{parts[0]} {parts[1]}"
        repeat = parts[2] if len(parts) > 2 else 'once'
        run_at = datetime.strptime(dt_str, '%Y-%m-%d %H:%M').isoformat()
        conn = get_db()
        conn.execute(
            'INSERT INTO scheduled_jobs (user_id, file_name, run_at, repeat, active, created_at) VALUES (?,?,?,?,1,?)',
            (uid, fname, run_at, repeat, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        bot.reply_to(message,
            f"✅ <b>Scheduled!</b>\n📄 <code>{fname}</code>\n⏰ {dt_str}\n🔁 {repeat}",
            parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, f"❌ Format galat hai!\nExample: 2025-01-15 08:00 daily\nError: {e}")

@bot.message_handler(commands=['myschedules'])
@security_check
def myschedules_cmd(message):
    uid = message.from_user.id
    track_command('myschedules', uid)
    conn = get_db()
    jobs = conn.execute(
        'SELECT * FROM scheduled_jobs WHERE user_id=? ORDER BY run_at DESC LIMIT 10', (uid,)
    ).fetchall()
    conn.close()
    if not jobs:
        bot.reply_to(message, "⏰ Koi scheduled job nahi.\nUse /schedule to add one.")
        return
    text = "╔══════════════════════════════════════╗\n║      ⏰ <b>YOUR SCHEDULES</b>              ║\n╠══════════════════════════════════════╣\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    for j in jobs:
        status = "🟢 Active" if j['active'] else "🔴 Done"
        text += f"║ {status}\n║ 📄 {j['file_name'][:20]}\n║ ⏰ {j['run_at'][:16]} ({j['repeat']})\n║ ─────────────────────\n"
        if j['active']:
            markup.add(types.InlineKeyboardButton(
                f"🗑️ Cancel: {j['file_name'][:20]}", callback_data=f"sched_cancel_{j['id']}"))
    text += "╚══════════════════════════════════════╝"
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("sched_cancel_"))
def sched_cancel_cb(call):
    job_id = int(call.data[13:])
    conn = get_db()
    conn.execute('UPDATE scheduled_jobs SET active=0 WHERE id=? AND user_id=?',
                 (job_id, call.from_user.id))
    conn.commit()
    conn.close()
    bot.answer_callback_query(call.id, "✅ Cancelled!")
    bot.send_message(call.message.chat.id, "✅ Scheduled job cancelled.")


# ============================================================
# 🎯 BOT TEMPLATES COMMANDS
# ============================================================

@bot.message_handler(commands=['templates'])
@security_check
def templates_cmd(message):
    uid = message.from_user.id
    track_command('templates', uid)
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, tmpl in BOT_TEMPLATES.items():
        markup.add(types.InlineKeyboardButton(
            f"{tmpl['name']} — {tmpl['desc'][:30]}",
            callback_data=f"tmpl_{key}"))
    bot.send_message(message.chat.id,
        "╔══════════════════════════════════════╗\n"
        "║     🎯 <b>BOT TEMPLATES</b>                ║\n"
        "╠══════════════════════════════════════╣\n"
        "║  Ready-made bots — ek click mein\n"
        "║  apne folder mein save ho jaate hain!\n"
        "╚══════════════════════════════════════╝\n"
        "Select a template:",
        parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("tmpl_"))
def template_cb(call):
    uid = call.from_user.id
    key = call.data[5:]
    tmpl = BOT_TEMPLATES.get(key)
    if not tmpl:
        bot.answer_callback_query(call.id, "❌ Template nahi mila!")
        return
    # Check file limit
    count = get_user_file_count(uid)
    limit = get_user_file_limit(uid)
    if count >= limit:
        bot.answer_callback_query(call.id, "❌ File limit reached!")
        return
    try:
        fname = tmpl['file']
        fpath = os.path.join(get_user_folder(uid), fname)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(tmpl['code'])
        with data_lock:
            if uid not in user_files:
                user_files[uid] = []
            user_files[uid] = [(n,t) for n,t in user_files[uid] if n != fname]
            user_files[uid].append((fname, 'py'))
        save_user_file_db(uid, fname, 'py', len(tmpl['code']))
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("▶️ Run Now", callback_data=f"run_{fname}"),
            types.InlineKeyboardButton("📝 Edit", callback_data=f"edit_open_{fname}"))
        markup.add(types.InlineKeyboardButton("📥 Download", callback_data=f"download_{fname}"))
        bot.answer_callback_query(call.id, "✅ Template added!")
        bot.send_message(call.message.chat.id,
            f"✅ <b>Template Added!</b>\n"
            f"📄 <code>{fname}</code>\n"
            f"📝 {tmpl['desc']}\n\n"
            f"⚠️ Pehle BOT_TOKEN set karo file mein,\nthen Run karo!",
            parse_mode='HTML', reply_markup=markup)
        log_action(uid, "TEMPLATE_USED", f"Template: {tmpl['name']}")
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Error!")
        bot.send_message(call.message.chat.id, f"❌ Error: {str(e)[:100]}")




# ============================================================
# 🔧 MAINTENANCE MODE
# ============================================================

maintenance_mode = False
maintenance_message = "🔧 Bot is under maintenance. Please try again later."

@bot.message_handler(commands=['maintenance'])
def maintenance_cmd(message):
    global maintenance_mode
    if message.from_user.id != OWNER_ID and message.from_user.id not in admin_ids:
        bot.reply_to(message, "❌ Owner only!")
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) > 1:
        global maintenance_message
        maintenance_message = parts[1]
    maintenance_mode = not maintenance_mode
    status = "🔧 ON" if maintenance_mode else "✅ OFF"
    bot.reply_to(message,
        f"╔══════════════════════════════════════╗\n"
        f"║       🔧 MAINTENANCE MODE             ║\n"
        f"╠══════════════════════════════════════╣\n"
        f"║  Status: {status}\n"
        f"║  Message: {maintenance_message[:30]}\n"
        f"╚══════════════════════════════════════╝",
        parse_mode='HTML')
    if maintenance_mode:
        notify_owner(f"🔧 Maintenance mode ENABLED by {message.from_user.id}")


# ─── Patch security_check to handle maintenance ───────────────
_orig_security_check = security_check
def security_check(func):
    @wraps(func)
    def wrapper(message, *args, **kwargs):
        uid = message.from_user.id if hasattr(message, 'from_user') else None
        if uid and maintenance_mode and uid not in admin_ids and uid != OWNER_ID:
            try:
                bot.reply_to(message, f"🔧 <b>Maintenance Mode</b>\n{maintenance_message}")
            except Exception:
                pass
            return
        return _orig_security_check(func)(message, *args, **kwargs)
    return wrapper


# ============================================================
# 👁️ FILE PREVIEW IN TELEGRAM
# ============================================================

@bot.message_handler(commands=['preview'])
@security_check
def preview_cmd(message):
    uid = message.from_user.id
    track_command('preview', uid)
    files = user_files.get(uid, [])
    previewable = [(n, t) for n, t in files if t in ('py','js','txt','json','yml','yaml','env')]
    if not previewable:
        bot.reply_to(message, "❌ No previewable files found!")
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for fname, ftype in previewable:
        icon = "🐍" if ftype == "py" else "🟨" if ftype == "js" else "📄"
        markup.add(types.InlineKeyboardButton(f"{icon} {fname[:30]}", callback_data=f"preview_{fname}"))
    bot.send_message(message.chat.id, "👁️ <b>File Preview</b>\nSelect file to preview:", parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("preview_"))
def preview_file_cb(call):
    uid = call.from_user.id
    fname = call.data[8:]
    fpath = os.path.join(get_user_folder(uid), fname)
    if not os.path.exists(fpath):
        bot.answer_callback_query(call.id, "❌ File not found!")
        return
    try:
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        size = os.path.getsize(fpath)
        lines = content.count('\n') + 1
        preview = content[:3000]
        bot.answer_callback_query(call.id)
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("▶️ Run", callback_data=f"run_{fname}"),
            types.InlineKeyboardButton("📝 Edit", callback_data=f"edit_open_{fname}"),
            types.InlineKeyboardButton("📥 Download", callback_data=f"download_{fname}"),
            types.InlineKeyboardButton("🔙 Back", callback_data="back_to_files"))
        bot.send_message(call.message.chat.id,
            f"👁️ <b>Preview: {fname}</b>\n"
            f"📏 Size: {format_size(size)} | 📄 Lines: {lines}\n\n"
            f"<code>{preview}</code>",
            parse_mode='HTML', reply_markup=markup)
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Preview error: {str(e)[:100]}")


# ============================================================
# 📝 RENAME & DUPLICATE FILE
# ============================================================

@bot.message_handler(commands=['rename'])
@security_check
def rename_cmd(message):
    uid = message.from_user.id
    track_command('rename', uid)
    files = user_files.get(uid, [])
    if not files:
        bot.reply_to(message, "❌ No files to rename!")
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for fname, ftype in files:
        markup.add(types.InlineKeyboardButton(f"✏️ {fname[:30]}", callback_data=f"rename_{fname}"))
    bot.send_message(message.chat.id, "✏️ <b>Rename File</b>\nSelect file to rename:", parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("rename_") and not c.data.startswith("rename_confirm_"))
def rename_file_cb(call):
    uid = call.from_user.id
    fname = call.data[7:]
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id,
        f"✏️ <b>Rename: {fname}</b>\n\nEnter new filename (with extension):\n"
        f"Example: <code>my_bot.py</code>\n\nCancel: /cancel",
        parse_mode='HTML')
    bot.register_next_step_handler(msg, process_rename, old_name=fname)

def process_rename(message, old_name):
    uid = message.from_user.id
    if message.text and message.text.strip() == '/cancel':
        bot.reply_to(message, "❌ Rename cancelled.")
        return
    new_name = message.text.strip() if message.text else ""
    if not new_name or '/' in new_name or '\\' in new_name or '..' in new_name:
        bot.reply_to(message, "❌ Invalid filename!")
        return
    user_folder = get_user_folder(uid)
    old_path = os.path.join(user_folder, old_name)
    new_path = os.path.join(user_folder, new_name)
    if not os.path.exists(old_path):
        bot.reply_to(message, "❌ File not found!")
        return
    if os.path.exists(new_path):
        bot.reply_to(message, "❌ A file with that name already exists!")
        return
    try:
        os.rename(old_path, new_path)
        with data_lock:
            files = user_files.get(uid, [])
            new_ext = new_name.split('.')[-1].lower() if '.' in new_name else 'txt'
            user_files[uid] = [(new_name if n == old_name else n, new_ext if n == old_name else t) for n, t in files]
        remove_user_file_db(uid, old_name)
        save_user_file_db(uid, new_name, new_name.split('.')[-1].lower() if '.' in new_name else 'txt', os.path.getsize(new_path))
        bot.reply_to(message,
            f"✅ <b>Renamed!</b>\n📄 {old_name} → <code>{new_name}</code>",
            parse_mode='HTML')
        log_action(uid, "FILE_RENAME", f"{old_name} → {new_name}")
    except Exception as e:
        bot.reply_to(message, f"❌ Rename failed: {str(e)[:100]}")

@bot.message_handler(commands=['duplicate'])
@security_check
def duplicate_cmd(message):
    uid = message.from_user.id
    track_command('duplicate', uid)
    files = user_files.get(uid, [])
    if not files:
        bot.reply_to(message, "❌ No files to duplicate!")
        return
    count = get_user_file_count(uid)
    limit = get_user_file_limit(uid)
    if count >= limit:
        bot.reply_to(message, f"❌ File limit reached ({count}/{int(limit) if limit != float('inf') else '∞'})!")
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for fname, ftype in files:
        markup.add(types.InlineKeyboardButton(f"📋 {fname[:30]}", callback_data=f"dup_{fname}"))
    bot.send_message(message.chat.id, "📋 <b>Duplicate File</b>\nSelect file to copy:", parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("dup_"))
def duplicate_file_cb(call):
    uid = call.from_user.id
    fname = call.data[4:]
    user_folder = get_user_folder(uid)
    src = os.path.join(user_folder, fname)
    if not os.path.exists(src):
        bot.answer_callback_query(call.id, "❌ File not found!")
        return
    base, ext = (fname.rsplit('.', 1) + [''])[:2] if '.' in fname else (fname, '')
    copy_name = f"{base}_copy.{ext}" if ext else f"{base}_copy"
    dst = os.path.join(user_folder, copy_name)
    n = 2
    while os.path.exists(dst):
        copy_name = f"{base}_copy{n}.{ext}" if ext else f"{base}_copy{n}"
        dst = os.path.join(user_folder, copy_name)
        n += 1
    try:
        shutil.copy2(src, dst)
        with data_lock:
            if uid not in user_files:
                user_files[uid] = []
            user_files[uid].append((copy_name, ext or 'txt'))
        save_user_file_db(uid, copy_name, ext or 'txt', os.path.getsize(dst))
        bot.answer_callback_query(call.id, "✅ Duplicated!")
        bot.send_message(call.message.chat.id,
            f"✅ <b>Duplicated!</b>\n📄 {fname} → <code>{copy_name}</code>",
            parse_mode='HTML')
        log_action(uid, "FILE_DUPLICATE", f"{fname} → {copy_name}")
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Error!")
        bot.send_message(call.message.chat.id, f"❌ Error: {str(e)[:100]}")


# ============================================================
# 📊 LEADERBOARD
# ============================================================

@bot.message_handler(commands=['leaderboard', 'top'])
@security_check
def leaderboard_cmd(message):
    uid = message.from_user.id
    track_command('leaderboard', uid)
    if not user_usage_stats:
        bot.reply_to(message, "📊 No data yet. Start using the bot!")
        return
    top_scripts = sorted(user_usage_stats.items(), key=lambda x: x[1]['scripts_run'], reverse=True)[:10]
    top_uploads = sorted(user_usage_stats.items(), key=lambda x: x[1]['uploads'], reverse=True)[:5]
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    text = (
        "╔══════════════════════════════════════╗\n"
        "║     🏆 <b>Dark Shadow LEADERBOARD</b> 🏆   ║\n"
        "╠══════════════════════════════════════╣\n"
        "║ <b>🤖 Top Script Runners:</b>\n"
    )
    for i, (luid, s) in enumerate(top_scripts):
        medal = medals[i] if i < len(medals) else "▪️"
        you = " 👈 You" if luid == uid else ""
        text += f"║ {medal} User {str(luid)[-4:]} — {s['scripts_run']} runs{you}\n"
    text += (
        "╠══════════════════════════════════════╣\n"
        "║ <b>📤 Top Uploaders:</b>\n"
    )
    for i, (luid, s) in enumerate(top_uploads):
        medal = medals[i] if i < len(medals) else "▪️"
        text += f"║ {medal} User {str(luid)[-4:]} — {s['uploads']} uploads\n"
    text += "╚══════════════════════════════════════╝"
    bot.send_message(message.chat.id, text, parse_mode='HTML')


# ============================================================
# 💰 REVENUE DASHBOARD
# ============================================================

@bot.message_handler(commands=['revenue'])
def revenue_cmd(message):
    if message.from_user.id != OWNER_ID and message.from_user.id not in admin_ids:
        bot.reply_to(message, "❌ Admin only!")
        return
    track_command('revenue', message.from_user.id)
    total_rev = sum(p.get('amount', 0) for p in payment_history)
    def _pay_month(p):
        ts = p.get('timestamp', None)
        try:
            if isinstance(ts, str):
                return datetime.fromisoformat(ts).month
            elif isinstance(ts, datetime):
                return ts.month
        except Exception:
            pass
        return -1
    this_month = sum(p.get('amount', 0) for p in payment_history if _pay_month(p) == datetime.now().month)
    plan_counts = {}
    for p in payment_history:
        plan = p.get('plan', 'unknown')
        plan_counts[plan] = plan_counts.get(plan, 0) + 1
    plan_text = "\n".join([f"║  {k}: {v} subs" for k, v in plan_counts.items()]) or "║  No sales yet"
    active_subs = len([u for u, d in user_subscriptions.items() if d['expiry'] > datetime.now()])
    text = (
        f"╔══════════════════════════════════════╗\n"
        f"║     💰 <b>REVENUE DASHBOARD</b> 💰         ║\n"
        f"╠══════════════════════════════════════╣\n"
        f"║  💵 Total Revenue: {total_rev} PKR\n"
        f"║  📅 This Month: {this_month} PKR\n"
        f"║  💳 Active Subs: {active_subs}\n"
        f"║  📦 Total Sales: {len(payment_history)}\n"
        f"╠══════════════════════════════════════╣\n"
        f"║ <b>📊 By Plan:</b>\n"
        f"{plan_text}\n"
        f"╠══════════════════════════════════════╣\n"
        f"║  ⏳ Pending Payments: {len(pending_payments)}\n"
        f"╚══════════════════════════════════════╝"
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML')


# ============================================================
# 🚀 GITHUB DEPLOY
# ============================================================

@bot.message_handler(commands=['gitdeploy'])
@security_check
def gitdeploy_cmd(message):
    uid = message.from_user.id
    track_command('gitdeploy', uid)
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message,
            "🚀 <b>GitHub Deploy</b>\n\n"
            "Usage: <code>/gitdeploy &lt;raw_file_url&gt;</code>\n\n"
            "Example:\n<code>/gitdeploy https://raw.githubusercontent.com/user/repo/main/bot.py</code>",
            parse_mode='HTML')
        return
    url = parts[1].strip()
    if not url.startswith('https://raw.githubusercontent.com/') and not url.startswith('https://gist.githubusercontent.com/'):
        bot.reply_to(message, "❌ Only raw GitHub/Gist URLs allowed!\nUse raw.githubusercontent.com links.")
        return
    count = get_user_file_count(uid)
    limit = get_user_file_limit(uid)
    if count >= limit:
        bot.reply_to(message, f"❌ File limit reached! ({count}/{int(limit) if limit != float('inf') else '∞'})")
        return
    msg = send_spinner_animation(message.chat.id, "🚀 Downloading from GitHub...", duration=2)
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            bot.edit_message_text(f"❌ Download failed! HTTP {resp.status_code}", message.chat.id, msg.message_id)
            return
        fname = url.split('/')[-1]
        if not fname or '.' not in fname:
            fname = 'github_bot.py'
        file_ext = fname.split('.')[-1].lower()
        allowed = ['py', 'js', 'json', 'txt', 'yml', 'yaml', 'env']
        if file_ext not in allowed:
            bot.edit_message_text(f"❌ Unsupported file type: .{file_ext}", message.chat.id, msg.message_id)
            return
        if len(resp.content) > MAX_FILE_SIZE_MB * 1024 * 1024:
            bot.edit_message_text(f"❌ File too large! Max {MAX_FILE_SIZE_MB}MB", message.chat.id, msg.message_id)
            return
        user_folder = get_user_folder(uid)
        file_path = os.path.join(user_folder, fname)
        with open(file_path, 'wb') as f:
            f.write(resp.content)
        with data_lock:
            if uid not in user_files:
                user_files[uid] = []
            user_files[uid] = [(n, t) for n, t in user_files[uid] if n != fname]
            user_files[uid].append((fname, file_ext))
        save_user_file_db(uid, fname, file_ext, len(resp.content))
        markup = types.InlineKeyboardMarkup(row_width=2)
        if file_ext in ('py', 'js'):
            markup.add(
                types.InlineKeyboardButton("▶️ Run Now", callback_data=f"run_{fname}"),
                types.InlineKeyboardButton("📝 Edit", callback_data=f"edit_open_{fname}"))
        markup.add(types.InlineKeyboardButton("📂 View Files", callback_data="back_to_files"))
        try:
            bot.edit_message_text(
                f"✅ <b>GitHub Deploy Success!</b>\n"
                f"📄 <code>{fname}</code>\n"
                f"📦 Size: {format_size(len(resp.content))}\n"
                f"🔗 From: {url[:50]}...",
                message.chat.id, msg.message_id, parse_mode='HTML', reply_markup=markup)
        except Exception:
            bot.send_message(message.chat.id, f"✅ Deployed: {fname}", reply_markup=markup)
        log_action(uid, "GITHUB_DEPLOY", f"Deployed {fname} from {url[:60]}")
        track_upload()
    except requests.Timeout:
        bot.edit_message_text("❌ Download timed out! Try again.", message.chat.id, msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)[:150]}", message.chat.id, msg.message_id)


# ============================================================
# ⚠️ CONFIG HEALTH CHECK
# ============================================================

def check_config_health():
    """Check critical config on startup and warn owner"""
    issues = []
    if TOKEN == 'YOUR_TOKEN_HERE':
        issues.append("❌ BOT_TOKEN not set in environment!")
    if OWNER_ID in (0, 7847937078):
        issues.append("⚠️ OWNER_ID still default — set your own ID in env!")
    if DASHBOARD_PASSWORD == 'darkshadow2024':
        issues.append("⚠️ Using default dashboard password — change DASHBOARD_PASS env!")
    if issues:
        logger.warning("CONFIG ISSUES: " + " | ".join(issues))
        try:
            bot.send_message(OWNER_ID,
                "⚠️ <b>Config Health Check</b>\n" + "\n".join(issues),
                parse_mode='HTML')
        except Exception:
            pass

@bot.message_handler(commands=['configcheck'])
def configcheck_cmd(message):
    if message.from_user.id != OWNER_ID and message.from_user.id not in admin_ids:
        bot.reply_to(message, "❌ Admin only!")
        return
    issues = []
    if TOKEN == 'YOUR_TOKEN_HERE':
        issues.append("❌ BOT_TOKEN not set!")
    if OWNER_ID in (0, 7847937078):
        issues.append("⚠️ OWNER_ID is default value!")
    if DASHBOARD_PASSWORD == 'darkshadow2024':
        issues.append("⚠️ Using default dashboard password!")
    if not os.path.exists(DATABASE_PATH):
        issues.append("⚠️ Database not created yet!")
    if issues:
        text = "⚠️ <b>Config Issues Found:</b>\n" + "\n".join(issues)
    else:
        text = "✅ <b>All config looks good!</b>"
    bot.reply_to(message, text, parse_mode='HTML')


# ============================================================
# 🔍 AUTO ERROR DETECT & FIX SUGGEST
# ============================================================

COMMON_ERRORS = {
    "ModuleNotFoundError": ("📦 Missing module! Install it via /install", "pip install <module_name>"),
    "SyntaxError": ("🔴 Syntax error in your code!", "Check indentation and brackets"),
    "ConnectionError": ("🌐 Network/connection error!", "Check your BOT_TOKEN and internet"),
    "Forbidden": ("🔒 Bot token invalid or bot blocked!", "Verify your BOT_TOKEN"),
    "JSONDecodeError": ("📄 JSON parsing failed!", "Check your JSON file format"),
    "PermissionError": ("🔑 Permission denied!", "Check file permissions"),
    "TimeoutError": ("⏱️ Connection timed out!", "Telegram API unreachable, retry"),
    "RecursionError": ("♾️ Infinite loop detected!", "Check your handler logic"),
    "MemoryError": ("🧠 Out of memory!", "Your script uses too much RAM"),
    "InvalidToken": ("🔑 Telegram token is invalid!", "Set correct BOT_TOKEN"),
}

def analyze_error(log_content):
    """Analyze log for known errors and suggest fixes"""
    for error_type, (msg, fix) in COMMON_ERRORS.items():
        if error_type in log_content:
            return msg, fix
    if "Traceback" in log_content:
        last_line = [l for l in log_content.strip().split("\n") if l.strip()]
        return f"❌ Script crashed!", last_line[-1][:100] if last_line else "Unknown error"
    return None, None

@bot.message_handler(commands=['diagnose'])
@security_check
def diagnose_cmd(message):
    uid = message.from_user.id
    track_command('diagnose', uid)
    files = user_files.get(uid, [])
    if not files:
        bot.reply_to(message, "❌ No files to diagnose!")
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for fname, ftype in files:
        if ftype in ('py', 'js'):
            markup.add(types.InlineKeyboardButton(f"🔍 {fname[:30]}", callback_data=f"diagnose_{fname}"))
    if not markup.keyboard:
        bot.reply_to(message, "❌ No Python/JS files to diagnose!")
        return
    bot.send_message(message.chat.id, "🔍 <b>Diagnose Script</b>\nSelect file:", parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("diagnose_"))
def diagnose_file_cb(call):
    uid = call.from_user.id
    fname = call.data[9:]
    log_path = os.path.join(LOGS_DIR, f"{uid}_{fname}.log")
    fpath = os.path.join(get_user_folder(uid), fname)
    bot.answer_callback_query(call.id, "🔍 Diagnosing...")
    diagnosis = []
    # Check log for errors
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            log = f.read()
        err_msg, fix = analyze_error(log)
        if err_msg:
            diagnosis.append(f"🔴 <b>Error Detected:</b> {err_msg}\n💡 <b>Fix:</b> {fix}")
    # Python syntax check
    if fname.endswith('.py') and os.path.exists(fpath):
        check = subprocess.run(
            [sys.executable, '-c', f'import ast; ast.parse(open("{fpath}").read())'],
            capture_output=True, text=True, timeout=10)
        if check.returncode != 0:
            diagnosis.append(f"🔴 <b>Syntax Error:</b>\n<code>{check.stderr[:200]}</code>")
        else:
            diagnosis.append("✅ Syntax OK")
    # Check file exists
    if os.path.exists(fpath):
        size = os.path.getsize(fpath)
        if size == 0:
            diagnosis.append("⚠️ File is empty!")
        else:
            diagnosis.append(f"✅ File exists ({format_size(size)})")
    else:
        diagnosis.append("❌ File missing from disk!")
    report = "\n\n".join(diagnosis) if diagnosis else "✅ No issues detected!"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data=f"file_{fname}"))
    bot.send_message(call.message.chat.id,
        f"🔍 <b>Diagnosis: {fname}</b>\n\n{report}",
        parse_mode='HTML', reply_markup=markup)


# ============================================================
# 🔔 SUBSCRIPTION EXPIRY ALERTS
# ============================================================

def check_expiring_subscriptions():
    """Notify users whose subs expire in 3 days or less"""
    while True:
        try:
            now = datetime.now()
            for uid, sub in list(user_subscriptions.items()):
                remaining = (sub['expiry'] - now).total_seconds()
                if 0 < remaining <= 3 * 86400:  # 3 days
                    days_left = int(remaining // 86400) + 1
                    try:
                        bot.send_message(uid,
                            f"⚠️ <b>Subscription Expiring Soon!</b>\n"
                            f"💳 Plan: {sub.get('plan','basic')}\n"
                            f"⏰ Expires in: {days_left} day(s)\n"
                            f"💰 Renew now: /buy",
                            parse_mode='HTML')
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"Expiry check error: {e}")
        time.sleep(86400)  # check daily

Thread(target=check_expiring_subscriptions, daemon=True).start()


# ============================================================
# 🤖 MULTI-RUN SCRIPTS
# ============================================================

@bot.message_handler(commands=['multirun'])
@security_check
def multirun_cmd(message):
    uid = message.from_user.id
    track_command('multirun', uid)
    files = user_files.get(uid, [])
    runnable = [(n, t) for n, t in files if t in ('py', 'js')]
    if not runnable:
        bot.reply_to(message, "❌ No runnable files!")
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for fname, ftype in runnable:
        running = is_bot_running(uid, fname)
        status = "🟢" if running else "🔴"
        markup.add(types.InlineKeyboardButton(f"{status} Run: {fname[:25]}", callback_data=f"run_{fname}"))
    markup.add(types.InlineKeyboardButton("🟢 Run ALL", callback_data="run_all_scripts"))
    bot.send_message(message.chat.id,
        "🚀 <b>Multi-Run</b>\nSelect scripts to run (or run all):",
        parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "run_all_scripts")
def run_all_scripts_cb(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id, "🚀 Starting all scripts...")
    files = user_files.get(uid, [])
    runnable = [(n, t) for n, t in files if t in ('py', 'js')]
    started = 0
    for fname, ftype in runnable:
        if not is_bot_running(uid, fname):
            user_folder = get_user_folder(uid)
            script_path = os.path.join(user_folder, fname)
            if os.path.exists(script_path):
                threading.Thread(
                    target=run_script_generic,
                    args=(script_path, uid, user_folder, fname, call.message, ftype),
                    daemon=True).start()
                started += 1
                time.sleep(0.5)
    bot.send_message(call.message.chat.id,
        f"🚀 <b>Started {started} script(s)!</b>\nUse /running to monitor.",
        parse_mode='HTML')


# ============================================================
# 🛑 FORCE STOP ALL (User)
# ============================================================

@bot.message_handler(commands=['killall'])
@security_check
def killall_cmd(message):
    uid = message.from_user.id
    track_command('killall', uid)
    stopped = 0
    for sk in [k for k in list(bot_scripts.keys()) if bot_scripts[k].get('user_id') == uid]:
        try:
            kill_process_tree(bot_scripts[sk])
            cleanup_script(sk)
            stopped += 1
        except Exception:
            pass
    bot.reply_to(message,
        f"🛑 <b>Force stopped {stopped} script(s)!</b>",
        parse_mode='HTML')


# ============================================================
# 🔧 .ENV FILE SUPPORT
# ============================================================

@bot.message_handler(commands=['setenv'])
@security_check
def setenv_cmd(message):
    uid = message.from_user.id
    track_command('setenv', uid)
    bot.reply_to(message,
        "🔧 <b>.env File Setup</b>\n\n"
        "Upload a .env file to set environment variables for your scripts.\n\n"
        "Format:\n<code>BOT_TOKEN=your_token_here\nAPI_KEY=your_api_key</code>\n\n"
        "📤 Just send your .env file now!",
        parse_mode='HTML')



# ============================================================
# 🧹 CLEANUP ON EXIT
# ============================================================

def cleanup_on_exit():
    logger.info("Cleaning up Dark Shadow...")
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
    logger.info("🤖 Starting Dark Shadow 🖤 Bot...")
    logger.info(f"📁 Base Dir: {BASE_DIR}")
    logger.info(f"💾 Database: {DATABASE_PATH}")
    logger.info("=" * 50)

    keep_alive()
    check_config_health()              # ✅ Config health warnings
    start_daily_report_scheduler()    # ✅ Daily report
    start_script_watchdog()           # ✅ Crash detection, runtime limit, auto-restart
    start_scheduler()                 # ✅ Scheduled jobs

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
