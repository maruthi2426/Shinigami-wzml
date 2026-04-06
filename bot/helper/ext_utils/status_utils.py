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


class EngineStatus:
    def __init__(self):
        ver = bot_cache.get("eng_versions", {})
        self.STATUS_ARIA2 = f"Aria2 v{ver.get('aria2', 'N/A')}"
        self.STATUS_AIOHTTP = f"AioHttp v{ver.get('aiohttp', 'N/A')}"
        self.STATUS_GDAPI = f"Google-API v{ver.get('gapi', 'N/A')}"
        self.STATUS_QBIT = f"qBit v{ver.get('qBittorrent', 'N/A')}"
        self.STATUS_TGRAM = f"Pyro v{ver.get('pyrotgfork', 'N/A')}"
        self.STATUS_MEGA = f"MegaCMD v{ver.get('mega', 'N/A')}"
        self.STATUS_YTDLP = f"yt-dlp v{ver.get('yt-dlp', 'N/A')}"
        self.STATUS_FFMPEG = f"ffmpeg v{ver.get('ffmpeg', 'N/A')}"
        self.STATUS_7Z = f"7z v{ver.get('7z', 'N/A')}"
        self.STATUS_RCLONE = f"RClone v{ver.get('rclone', 'N/A')}"
        self.STATUS_SABNZBD = f"SABnzbd+ v{ver.get('SABnzbd+', 'N/A')}"
        self.STATUS_QUEUE = "QSystem v2"
        self.STATUS_JD = "JDownloader v2"
        self.STATUS_YT = "Youtube-Api"
        self.STATUS_METADATA = "Metadata"
        self.STATUS_UPHOSTER = "Uphoster"


# 🔥 ULTRA PREMIUM STATUS EMOJI MAP v2.0 - NEVER BEFORE SEEN AESTHETIC
# Each emoji combo is hand-crafted for maximum visual impact + meaning
STATUS_EMOJIS = {
    MirrorStatus.STATUS_DOWNLOAD: "🚀⬇️⚡",
    MirrorStatus.STATUS_UPLOAD: "✨⬆️🌟",
    MirrorStatus.STATUS_CLONE: "♻️🔄💫",
    MirrorStatus.STATUS_QUEUEDL: "⏳📥🔥",
    MirrorStatus.STATUS_QUEUEUP: "⏳📤💎",
    MirrorStatus.STATUS_PAUSED: "⏸️❄️🧊",
    MirrorStatus.STATUS_ARCHIVE: "📦🔐🛡️",
    MirrorStatus.STATUS_EXTRACT: "📤🔓✨",
    MirrorStatus.STATUS_SPLIT: "✂️📑⚔️",
    MirrorStatus.STATUS_CHECK: "🔍✅🧬",
    MirrorStatus.STATUS_SEED: "🌱🚀💚",
    MirrorStatus.STATUS_SAMVID: "🎬📼🔥",
    MirrorStatus.STATUS_CONVERT: "🔄🧪🧬",
    MirrorStatus.STATUS_FFMPEG: "🎞️⚙️🎥",
    MirrorStatus.STATUS_YT: "📺🔥🎯",
    MirrorStatus.STATUS_METADATA: "📋✨🧠",
}


# 🔥 ULTRA PREMIUM PROGRESS BAR v2.0 - 30 segments, true gradient + glow effect
def get_progress_bar_string(pct):
    try:
        pct_float = float(str(pct).strip("%"))
    except:
        pct_float = 0.0
    p = min(max(pct_float, 0), 100)
    filled = int(round(p / (100 / 30)))  # 30 ultra-fine segments
    # Gradient blocks: full → near-full → empty with premium Unicode
    gradient = "█" * filled + "▓" * max(0, min(8, 30 - filled)) + "░" * (30 - filled)
    # Add glowing percentage with sparkle if >95%
    percent_str = f"<b>{p:.1f}%</b>"
    if p >= 95:
        percent_str = f"🌟<b>{p:.1f}%</b>🌟"
    return f"<b>[</b>{gradient}<b>]</b> {percent_str}"


STATUSES = {
    "ALL": "All",
    "DL": MirrorStatus.STATUS_DOWNLOAD,
    "UP": MirrorStatus.STATUS_UPLOAD,
    "QD": MirrorStatus.STATUS_QUEUEDL,
    "QU": MirrorStatus.STATUS_QUEUEUP,
    "AR": MirrorStatus.STATUS_ARCHIVE,
    "EX": MirrorStatus.STATUS_EXTRACT,
    "SD": MirrorStatus.STATUS_SEED,
    "CL": MirrorStatus.STATUS_CLONE,
    "CM": MirrorStatus.STATUS_CONVERT,
    "SP": MirrorStatus.STATUS_SPLIT,
    "SV": MirrorStatus.STATUS_SAMVID,
    "FF": MirrorStatus.STATUS_FFMPEG,
    "PA": MirrorStatus.STATUS_PAUSED,
    "CK": MirrorStatus.STATUS_CHECK,
    "YT": MirrorStatus.STATUS_YT,
    "MD": MirrorStatus.STATUS_METADATA,
}


async def get_task_by_gid(gid: str):
    async with task_dict_lock:
        for tk in task_dict.values():
            if hasattr(tk, "seeding"):
                await tk.update()
            if tk.gid() == gid:
                return tk
        return None


async def get_specific_tasks(status, user_id):
    if status == "All":
        if user_id:
            return [tk for tk in task_dict.values() if tk.listener.user_id == user_id]
        else:
            return list(task_dict.values())
    tasks_to_check = (
        [tk for tk in task_dict.values() if tk.listener.user_id == user_id]
        if user_id
        else list(task_dict.values())
    )
    coro_tasks = [tk for tk in tasks_to_check if iscoroutinefunction(tk.status)]
    coro_statuses = await gather(*[tk.status() for tk in coro_tasks]) if coro_tasks else []
    result = []
    coro_index = 0
    for tk in tasks_to_check:
        st = coro_statuses[coro_index] if tk in coro_tasks else tk.status()
        if tk in coro_tasks:
            coro_index += 1
        if (st == status) or (status == MirrorStatus.STATUS_DOWNLOAD and st not in STATUSES.values()):
            result.append(tk)
    return result


async def get_all_tasks(req_status: str, user_id):
    async with task_dict_lock:
        return await get_specific_tasks(req_status, user_id)


def get_raw_file_size(size):
    num, unit = size.split()
    return int(float(num) * (1024 ** SIZE_UNITS.index(unit)))


def get_readable_file_size(size_in_bytes):
    if not size_in_bytes:
        return "0B"
    index = 0
    while size_in_bytes >= 1024 and index < len(SIZE_UNITS) - 1:
        size_in_bytes /= 1024
        index += 1
    return f"{size_in_bytes:.2f}{SIZE_UNITS[index]}"


def get_readable_time(seconds: int):
    periods = [("d", 86400), ("h", 3600), ("m", 60), ("s", 1)]
    result = ""
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result += f"{int(period_value)}{period_name}"
    return result or "0s"


def get_raw_time(time_str: str) -> int:
    time_units = {"d": 86400, "h": 3600, "m": 60, "s": 1}
    return sum(int(value) * time_units[unit] for value, unit in findall(r"(\d+)([dhms])", time_str))


def time_to_seconds(time_duration):
    try:
        parts = time_duration.split(":")
        if len(parts) == 3:
            hours, minutes, seconds = map(float, parts)
        elif len(parts) == 2:
            hours = 0
            minutes, seconds = map(float, parts)
        elif len(parts) == 1:
            hours = 0
            minutes = 0
            seconds = float(parts[0])
        else:
            return 0
        return hours * 3600 + minutes * 60 + seconds
    except Exception:
        return 0


def speed_string_to_bytes(size_text: str):
    size = 0
    size_text = size_text.lower()
    if "k" in size_text:
        size += float(size_text.split("k")[0]) * 1024
    elif "m" in size_text:
        size += float(size_text.split("m")[0]) * 1048576
    elif "g" in size_text:
        size += float(size_text.split("g")[0]) * 1073741824
    elif "t" in size_text:
        size += float(size_text.split("t")[0]) * 1099511627776
    elif "b" in size_text:
        size += float(size_text.split("b")[0])
    return size


# ─────────────────────────────────────────────────────────────────────────────
# 🔥 CORE PREMIUM MESSAGE BUILDER v2.0 - NEVER BEFORE SEEN IN ANY MIRROR BOT
# Advanced card-style layout, dynamic separators, GID, subname, enhanced stats
# ─────────────────────────────────────────────────────────────────────────────
async def get_readable_message(sid, is_user, page_no=1, status="All", page_step=1):
    msg = "<b>🔥 ULTRA PREMIUM MIRROR STATUS v2.0 🔥</b>\n"
    msg += "<i>Advanced • Aesthetic • Real-time</i>\n\n"
    button = None

    tasks = await get_specific_tasks(status, sid if is_user else None)
    STATUS_LIMIT = Config.STATUS_LIMIT
    tasks_no = len(tasks)
    pages = (max(tasks_no, 1) + STATUS_LIMIT - 1) // STATUS_LIMIT

    # Smart pagination with wrap-around
    if page_no > pages:
        page_no = (page_no - 1) % pages + 1
        status_dict[sid]["page_no"] = page_no
    elif page_no < 1:
        page_no = pages - (abs(page_no) % pages) + 1 if pages > 0 else 1
        status_dict[sid]["page_no"] = page_no

    start_position = (page_no - 1) * STATUS_LIMIT
    displayed_tasks = tasks[start_position : STATUS_LIMIT + start_position]

    for index, task in enumerate(displayed_tasks, start=1):
        if status != "All":
            tstatus = status
        elif iscoroutinefunction(task.status):
            tstatus = await task.status()
        else:
            tstatus = task.status()

        emoji = STATUS_EMOJIS.get(tstatus, "🔥")
        task_index = index + start_position
        gid = task.gid()

        # ──────── PREMIUM TASK CARD ────────
        msg += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"<b>{task_index}. {emoji} {tstatus.upper()}</b> <code>[{gid}]</code>\n"
        msg += f"📁 <b><i>{escape(task.name())}</i></b>\n"

        if task.listener.subname:
            msg += f"📝 <i>{escape(task.listener.subname)}</i>\n"

        # User + Link
        user_mention = task.listener.message.from_user.mention(style='html')
        msg += f"👤 <b>Task By:</b> {user_mention} <code>(#{task.listener.message.from_user.id})</code>"
        if task.listener.is_super_chat:
            msg += f" <a href='{task.listener.message.link}'>🔗 View Original</a>"
        msg += "\n"

        elapsed = time() - task.listener.message.date.timestamp()

        # ──────── DYNAMIC CONTENT SECTION (core advanced logic) ────────
        if tstatus not in [MirrorStatus.STATUS_SEED, MirrorStatus.STATUS_QUEUEUP] and task.listener.progress:
            # ACTIVE TASK (Download / Upload / Process)
            progress = task.progress()
            bar = get_progress_bar_string(progress)

            msg += f"\n{bar}\n\n"

            subsize = ""
            count = ""
            if task.listener.subname:
                subsize = f" / {get_readable_file_size(task.listener.subsize)}"
                ac = len(task.listener.files_to_proceed)
                count = f" <b>({task.listener.proceed_count}/{ac or '?'})</b>"

            msg += f"📏 <b>Size:</b> <i>{task.size()}</i>\n"
            msg += f"📦 <b>Processed:</b> <i>{task.processed_bytes()}{subsize}</i>{count}\n"
            msg += f"⚡ <b>Speed:</b> <i>{task.speed()}</i>\n"
            msg += f"⏳ <b>ETA:</b> <i>{task.eta()}</i> • <b>Total Time:</b> <i>{get_readable_time(elapsed + get_raw_time(task.eta()))}</i>\n"
            msg += f"⏰ <b>Elapsed:</b> <i>{get_readable_time(elapsed)}</i>\n"

            if tstatus == MirrorStatus.STATUS_DOWNLOAD and (task.listener.is_torrent or task.listener.is_qbit):
                try:
                    msg += f"👥 <b>Seeders:</b> {task.seeders_num()} | <b>Leechers:</b> {task.leechers_num()}\n"
                except:
                    pass

        elif tstatus == MirrorStatus.STATUS_SEED:
            # SEEDING - Special premium layout
            msg += f"🌱 <b>Size:</b> <i>{task.size()}</i>\n"
            msg += f"⬆️ <b>Uploaded:</b> <i>{task.uploaded_bytes()}</i>\n"
            msg += f"⚡ <b>Speed:</b> <i>{task.seed_speed()}</i>\n"
            msg += f"📈 <b>Ratio:</b> <i>{task.ratio()}</i>\n"
            msg += f"⏰ <b>Seeding Time:</b> <i>{task.seeding_time()}</i> • <b>Elapsed:</b> <i>{get_readable_time(elapsed)}</i>\n"

        else:
            # QUEUED / PAUSED / STATIC
            msg += f"📏 <b>Size:</b> <i>{task.size()}</i>\n"

        # Engine & Mode - Always shown
        msg += f"🚀 <b>Engine:</b> <i>{task.engine}</i>\n"
        msg += f"🔄 <b>In Mode:</b> <i>{task.listener.mode[0]}</i> | <b>Out Mode:</b> <i>{task.listener.mode[1]}</i>\n"

        # Cancel command (premium style)
        from ..telegram_helper.bot_commands import BotCommands
        msg += f"❌ <b>Stop Task:</b> <code>/{BotCommands.CancelTaskCommand[1]}_{gid}</code>\n\n"

    # No tasks case - ultra premium
    if not displayed_tasks:
        if status == "All":
            return None, None
        else:
            msg = f"🌟 <b>NO ACTIVE {status.upper()} TASKS!</b>\n\n"
            msg += "✨ Bot is idle and ready for new mirrors!\n"
            msg += "🔥 Start a task to see the magic happen...\n\n"

    # ──────── PAGE INFO & NAVIGATION ────────
    if len(tasks) > STATUS_LIMIT:
        msg += f"📑 <b>Page {page_no}/{pages}</b> | 📊 <b>{tasks_no} Tasks Total</b> | Step {page_step}\n"

    # Buttons
    buttons = ButtonMaker()
    if not is_user:
        buttons.data_button("📜 Overview", f"status {sid} ov", position="header")
    if len(tasks) > STATUS_LIMIT:
        buttons.data_button("⬅️ Prev", f"status {sid} pre", position="header")
        buttons.data_button("➡️ Next", f"status {sid} nex", position="header")
        if tasks_no > 30:
            for i in [1, 2, 4, 6, 8, 10, 15]:
                buttons.data_button(f"⏭️{i}", f"status {sid} ps {i}", position="footer")
    if status != "All" or tasks_no > 20:
        for label, status_value in STATUSES.items():
            if status_value != status:
                buttons.data_button(label, f"status {sid} st {status_value}")
    buttons.data_button("🔄 Refresh Now", f"status {sid} ref", position="header")
    button = buttons.build_menu(8)

    # ──────── PREMIUM BOT STATS FOOTER v2.0 ────────
    free_space = get_readable_file_size(disk_usage(DOWNLOAD_DIR).free)
    free_pct = round(100 - disk_usage(DOWNLOAD_DIR).percent, 1)
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"🔥 <b><u>BOT LIVE STATS</u></b> 🔥\n"
    msg += f"💻 <b>CPU:</b> {cpu_percent()}% | 🧠 <b>RAM:</b> {virtual_memory().percent}%\n"
    msg += f"🗄️ <b>Free Storage:</b> {free_space} <i>[{free_pct}%]</i>\n"
    msg += f"⏳ <b>Uptime:</b> {get_readable_time(time() - bot_start_time)}\n"
    msg += f"<i>Powered by Ultra Premium Core • {time():.0f}</i>"

    return msg, button
