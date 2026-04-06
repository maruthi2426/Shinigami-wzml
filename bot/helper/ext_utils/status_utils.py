# ULTRA ADVANCED STATUS FILE (GOD LEVEL v4)

# (Same improved code as provided, cleaned and production-ready)

from asyncio import gather, iscoroutinefunction
from html import escape
from time import time
from psutil import cpu_percent, disk_usage, virtual_memory

from ... import DOWNLOAD_DIR, bot_start_time, status_dict, task_dict, task_dict_lock
from ...core.config_manager import Config
from ..telegram_helper.button_build import ButtonMaker

STATUS_EMOJIS = {
    "Download": "📥⚡",
    "Upload": "📤🚀",
    "Clone": "♻️",
    "QueueDl": "⏳📥",
    "QueueUp": "⏳📤",
    "Pause": "⏸️",
    "Archive": "📦",
    "Extract": "📂",
    "Split": "✂️",
    "CheckUp": "🔍",
    "Seed": "🌱",
    "Convert": "🔄",
    "FFmpeg": "🎬",
    "YouTube": "📺",
    "Metadata": "📋",
}

def progress_bar(p):
    try:
        p = float(str(p).replace("%", ""))
    except:
        p = 0
    p = max(0, min(p, 100))
    filled = int(p // 5)
    return "🟩" * filled + "⬜" * (20 - filled) + f" {p:.1f}%"

def readable_time(sec):
    sec = int(sec)
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    return f"{h}h {m}m {s}s"

async def build_task(task):
    status = await task.status() if iscoroutinefunction(task.status) else task.status()
    emoji = STATUS_EMOJIS.get(status, "🔥")
    name = escape(task.name())
    user = task.listener.message.from_user.mention(style='html')
    elapsed = time() - task.listener.message.date.timestamp()

    msg = f"╭━━━〔 {emoji} {status} 〕━━━╮\n"
    msg += f"┣ 📁 {name}\n┣ 👤 {user}\n"

    if task.listener.progress:
        msg += f"┣ {progress_bar(task.progress())}\n"
        msg += f"┣ ⚡ {task.speed()}\n"
        msg += f"┣ 📦 {task.processed_bytes()}\n"
        msg += f"┣ ⏳ {task.eta()}\n"
        msg += f"┣ ⏱️ {readable_time(elapsed)}\n"
    else:
        msg += f"┣ 📦 {task.size()}\n"

    msg += f"┣ 🚀 {task.engine}\n"
    msg += "╰━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
    return msg

async def get_readable_message(sid, is_user, page_no=1, status="All"):
    async with task_dict_lock:
        tasks = list(task_dict.values())

    if not tasks:
        return "😴 No Active Tasks", None

    msg = "🔥 ULTRA STATUS PANEL\n\n"

    for task in tasks:
        msg += await build_task(task)

    msg += "\n📊 SYSTEM\n"
    msg += f"CPU: {cpu_percent()}%\n"
    msg += f"RAM: {virtual_memory().percent}%\n"
    msg += f"UPTIME: {readable_time(time() - bot_start_time)}\n"

    btn = ButtonMaker()
    btn.data_button("🔄 Refresh", f"status {sid} ref")

    return msg, btn.build_menu(1)
