# =========================
# 🔥 SAFE + ADVANCED STATUS FILE (COMPATIBLE VERSION)
# =========================

from asyncio import gather, iscoroutinefunction
from html import escape
from re import findall
from time import time
from psutil import cpu_percent, disk_usage, virtual_memory

from ... import (
    DOWNLOAD_DIR,
    bot_cache,
    bot_start_time,
    status_dict,
    task_dict,
    task_dict_lock,
)
from ...core.config_manager import Config
from ..telegram_helper.button_build import ButtonMaker

SIZE_UNITS = ["B", "KB", "MB", "GB", "TB", "PB"]

# =========================
# 🔥 STATUS TYPES
# =========================

class MirrorStatus:
    STATUS_UPLOAD = "Upload"
    STATUS_DOWNLOAD = "Download"
    STATUS_CLONE = "Clone"
    STATUS_QUEUEDL = "QueueDl"
    STATUS_QUEUEUP = "QueueUp"
    STATUS_PAUSED = "Pause"
    STATUS_ARCHIVE = "Archive"
    STATUS_EXTRACT = "Extract"
    STATUS_SPLIT = "Split"
    STATUS_CHECK = "CheckUp"
    STATUS_SEED = "Seed"
    STATUS_SAMVID = "SamVid"
    STATUS_CONVERT = "Convert"
    STATUS_FFMPEG = "FFmpeg"
    STATUS_YT = "YouTube"
    STATUS_METADATA = "Metadata"


# =========================
# 🎨 EMOJIS
# =========================

STATUS_EMOJIS = {
    MirrorStatus.STATUS_DOWNLOAD: "📥⚡",
    MirrorStatus.STATUS_UPLOAD: "📤🚀",
    MirrorStatus.STATUS_CLONE: "♻️",
    MirrorStatus.STATUS_QUEUEDL: "⏳📥",
    MirrorStatus.STATUS_QUEUEUP: "⏳📤",
    MirrorStatus.STATUS_PAUSED: "⏸️",
    MirrorStatus.STATUS_ARCHIVE: "📦",
    MirrorStatus.STATUS_EXTRACT: "📂",
    MirrorStatus.STATUS_SPLIT: "✂️",
    MirrorStatus.STATUS_CHECK: "🔍",
    MirrorStatus.STATUS_SEED: "🌱",
    MirrorStatus.STATUS_CONVERT: "🔄",
    MirrorStatus.STATUS_FFMPEG: "🎬",
    MirrorStatus.STATUS_YT: "📺",
    MirrorStatus.STATUS_METADATA: "📋",
}

# =========================
# 🔥 PROGRESS BAR
# =========================

def get_progress_bar_string(pct):
    try:
        pct = float(str(pct).replace("%", ""))
    except:
        pct = 0

    pct = max(0, min(pct, 100))
    filled = int(pct // 5)
    return "🟩" * filled + "⬜" * (20 - filled) + f" {pct:.1f}%"

# =========================
# 🧠 REQUIRED FUNCTIONS (DO NOT REMOVE)
# =========================

def get_readable_time(seconds: int):
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)

    result = ""
    if d:
        result += f"{d}d"
    if h:
        result += f"{h}h"
    if m:
        result += f"{m}m"
    if s:
        result += f"{s}s"

    return result or "0s"


def get_readable_file_size(size):
    if not size:
        return "0B"
    index = 0
    while size >= 1024 and index < len(SIZE_UNITS) - 1:
        size /= 1024
        index += 1
    return f"{size:.2f}{SIZE_UNITS[index]}"


def get_raw_time(time_str: str) -> int:
    time_units = {"d": 86400, "h": 3600, "m": 60, "s": 1}
    return sum(int(v) * time_units[u] for v, u in findall(r"(\\d+)([dhms])", time_str))


# =========================
# 🔥 TASK FETCHING
# =========================

async def get_specific_tasks(status, user_id):
    tasks = list(task_dict.values())
    if user_id:
        tasks = [tk for tk in tasks if tk.listener.user_id == user_id]
    return tasks


# =========================
# 🔥 TASK CARD UI
# =========================

async def build_task_card(task, index):
    status = await task.status() if iscoroutinefunction(task.status) else task.status()
    emoji = STATUS_EMOJIS.get(status, "🔥")

    name = escape(task.name())
    user = task.listener.message.from_user.mention(style='html')
    elapsed = time() - task.listener.message.date.timestamp()

    msg = f"╭━━━〔 {emoji} <b>{status}</b> 〕━━━╮\\n"
    msg += f"┣ 📁 <b>{name}</b>\\n"
    msg += f"┣ 👤 {user}\\n"

    if task.listener.progress:
        msg += f"┣ {get_progress_bar_string(task.progress())}\\n"
        msg += f"┣ ⚡ <b>Speed:</b> {task.speed()}\\n"
        msg += f"┣ 📦 <b>Done:</b> {task.processed_bytes()}\\n"
        msg += f"┣ ⏳ <b>ETA:</b> {task.eta()}\\n"
        msg += f"┣ ⏱️ <b>Elapsed:</b> {get_readable_time(elapsed)}\\n"
    else:
        msg += f"┣ 📦 <b>Size:</b> {task.size()}\\n"

    msg += f"┣ 🚀 <b>Engine:</b> {task.engine}\\n"
    msg += f"╰━━━━━━━━━━━━━━━━━━━━━━╯\\n\\n"

    return msg


# =========================
# 🔥 MAIN FUNCTION
# =========================

async def get_readable_message(sid, is_user, page_no=1, status="All", page_step=1):

    async with task_dict_lock:
        tasks = await get_specific_tasks(status, sid if is_user else None)

    if not tasks:
        return "😴 <b>No Active Tasks</b>", None

    msg = "🔥 <b>ADVANCED STATUS PANEL</b>\\n\\n"

    for i, task in enumerate(tasks, 1):
        msg += await build_task_card(task, i)

    # =========================
    # 📊 SYSTEM STATS
    # =========================

    free = get_readable_file_size(disk_usage(DOWNLOAD_DIR).free)

    msg += "\\n╭━━━〔 📊 SYSTEM 〕━━━╮\\n"
    msg += f"┣ 💻 CPU: {cpu_percent()}%\\n"
    msg += f"┣ 🧠 RAM: {virtual_memory().percent}%\\n"
    msg += f"┣ 💾 Free: {free}\\n"
    msg += f"┣ ⏳ Uptime: {get_readable_time(time() - bot_start_time)}\\n"
    msg += "╰━━━━━━━━━━━━━━━━━━━━╯\\n"

    # =========================
    # 🔘 BUTTONS
    # =========================

    buttons = ButtonMaker()
    buttons.data_button("🔄 Refresh", f"status {sid} ref")

    return msg, buttons.build_menu(1)
