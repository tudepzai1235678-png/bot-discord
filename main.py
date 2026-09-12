# -*- coding: utf-8 -*-
import csv
import json
import os
import re
import time
import unicodedata
import urllib.request
import discord
from discord.ext import commands

# Cấu hình Bot Discord với tiền tố lệnh là dấu chấm (.)
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

# =========================================================
# LẤY TOKEN VÀ CHANNEL ID TỪ BIẾN MÔI TRƯỜNG (ENVIRONMENT)
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "123456789012345678"))
# =========================================================

# LINK DỮ LIỆU ONLINE TRỰC TIẾP TỪ GITHUB REPO: LeMinhVoid-VnxD/DecodeFullMW
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/LeMinhVoid-VnxD/DecodeFullMW/main/01_Nguon_MiniWorld_Data410/02_Lua_Scripts_va_Bang_CSV_script_res/script/language/vie/csvdef/utf8"


def remove_accents(input_str):
    if not input_str:
        return ""
    nfkd_form = unicodedata.normalize("NFKD", input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()


def fetch_csv_from_github(file_name):
    """Tải file CSV trực tiếp từ GitHub Repo"""
    url = f"{GITHUB_RAW_BASE}/{file_name}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            return list(csv.reader(content.splitlines()))
    except Exception as e:
        print(f"⚠️ Không thể tải {file_name} từ GitHub: {e}")
        return []


# --- CLASS QUẢN LÝ DỮ LIỆU GAME (ITEMS, MONSTERS, APIS, BUFFS) ---
class MiniWorldDatabase:

    def __init__(self):
        self.items = []
        self.monsters = []
        self.apis = []
        self.buffs = []
        self.loaded = False

    def load_data(self):
        if self.loaded:
            return

        print("🔄 Đang tải dữ liệu Mini World trực tiếp từ GitHub...")
        self._load_items()
        self._load_monsters()
        self._load_apis()
        self._load_buffs()
        self.loaded = True

        total_count = (
            len(self.items) + len(self.monsters) + len(self.apis) + len(self.buffs)
        )
        print(f"✅ [DATABASE ONLINE] Đã tải thành công {total_count} bản ghi từ GitHub!")

    def _load_items(self):
        rows = fetch_csv_from_github("itemdef.csv")
        if len(rows) < 3:
            return
        for row in rows[2:]:
            if len(row) >= 2 and row[0].strip():
                item_id = row[0].strip()
                name = row[1].strip() if len(row) > 1 else ""
                desc = row[2].strip() if len(row) > 2 else ""
                get_way = row[3].strip() if len(row) > 3 else ""
                if name != "@Null@" and name != "":
                    self.items.append(
                        {
                            "type": "Vật Phẩm / Khối",
                            "id": item_id,
                            "name": name,
                            "desc": desc,
                            "extra": get_way,
                            "norm_name": remove_accents(name),
                        }
                    )

    def _load_monsters(self):
        rows = fetch_csv_from_github("monster.csv")
        if len(rows) < 3:
            return
        for row in rows[2:]:
            if len(row) >= 2 and row[0].strip():
                mid = row[0].strip()
                name = row[1].strip() if len(row) > 1 else ""
                desc = row[2].strip() if len(row) > 2 else ""
                if name != "@Null@" and name != "":
                    self.monsters.append(
                        {
                            "type": "Sinh Vật / Quái Vật",
                            "id": mid,
                            "name": name,
                            "desc": desc,
                            "extra": "",
                            "norm_name": remove_accents(name),
                        }
                    )

    def _load_apis(self):
        rows = fetch_csv_from_github("scriptapi.csv")
        if len(rows) < 3:
            return
        for row in rows[2:]:
            if len(row) >= 4 and row[0].strip():
                api_id = row[0].strip()
                type_name = row[1].strip() if len(row) > 1 else ""
                func_name = row[2].strip() if len(row) > 2 else ""
                func_desc = row[3].strip() if len(row) > 3 else ""
                params = row[4].strip() if len(row) > 4 else ""
                returns = row[5].strip() if len(row) > 5 else ""
                explain = row[6].strip() if len(row) > 6 else ""
                example = row[7].strip() if len(row) > 7 else ""
                self.apis.append(
                    {
                        "type": "Lua Script API",
                        "id": api_id,
                        "name": f"{type_name}:{func_name}",
                        "desc": explain or func_desc,
                        "syntax": func_desc,
                        "params": params,
                        "returns": returns,
                        "example": example,
                        "norm_name": remove_accents(
                            f"{type_name} {func_name} {explain}"
                        ),
                    }
                )

    def _load_buffs(self):
        rows = fetch_csv_from_github("buffdef.csv")
        if len(rows) < 3:
            return
        for row in rows[2:]:
            if len(row) >= 2 and row[0].strip():
                bid = row[0].strip()
                name = row[1].strip() if len(row) > 1 else ""
                desc = row[2].strip() if len(row) > 2 else ""
                if name != "@Null@" and name != "":
                    self.buffs.append(
                        {
                            "type": "Hiệu Ứng Buff",
                            "id": bid,
                            "name": name,
                            "desc": desc,
                            "extra": "",
                            "norm_name": remove_accents(name),
                        }
                    )

    def search(self, query, category="all", limit=5):
        self.load_data()
        q_norm = remove_accents(query.strip())
        q_orig = query.strip().lower()
        results = []

        pool = []
        if category in ["all", "item"]:
            pool.extend(self.items)
        if category in ["all", "monster"]:
            pool.extend(self.monsters)
        if category in ["all", "api"]:
            pool.extend(self.apis)
        if category in ["all", "buff"]:
            pool.extend(self.buffs)

        for entry in pool:
            matched = False
            if q_orig == entry["id"] or q_orig in entry["id"]:
                matched = True
            elif q_norm in entry["norm_name"]:
                matched = True
            elif q_orig in entry["name"].lower():
                matched = True
            elif "syntax" in entry and q_orig in entry["syntax"].lower():
                matched = True

            if matched:
                results.append(entry)
                if len(results) >= limit:
                    break

        return results


mw_db = MiniWorldDatabase()


def format_timestamp(ts):
    if not ts or ts == -1:
        return "Vĩnh viễn"
    try:
        return time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(ts))
    except Exception:
        return str(ts)


def get_part_name(part_id):
    parts = {
        1: "Mũ / Tóc (Part 1)",
        2: "Khuôn mặt (Part 2)",
        3: "Áo / Thân trên (Part 3)",
        4: "Quần / Thân dưới (Part 4)",
        7: "Lưng / Cánh (Part 7)",
        8: "Hiệu ứng / Chân (Part 8)",
        9: "Phụ kiện đi kèm (Part 9)",
    }
    return parts.get(part_id, f"Phụ kiện (Part {part_id})")


def query_live_server(input_id):
    candidates = [
        input_id,
        f"1{input_id}",
        f"10{input_id}",
        f"11{input_id}",
        f"100{input_id}",
    ]
    headers = {"User-Agent": "MiniWorldClient/0.46.0"}

    for uin in candidates:
        url = f"http://update.miniworldgame.com:6000/miscquery/query_avatar_list_by_uin/?uin={uin}"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=3) as resp:
                res = json.loads(resp.read().decode("utf-8", errors="ignore"))
                if res.get("code") == 0 and res.get("msg"):
                    return uin, res["msg"], url
        except Exception:
            pass
    return None, None, None


# --- BOT EVENTS & COMMANDS ---
@bot.event
async def on_ready():
    mw_db.load_data()
    print(f"✅ Bot đã kết nối thành công: {bot.user.name}")

    if CHANNEL_ID:
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="🟢 CỔNG MÁY CHỦ BOT TRA CỨU ĐÃ HOẠT ĐỘNG",
                description=(
                    "Hệ thống tra cứu dữ liệu Mini World đã sẵn sàng!\n"
                    "• Gõ `.check <ID>` để tra cứu người chơi.\n"
                    "• Gõ `.find <từ khóa>` để tra cứu Vật phẩm / Quái vật / API Lua / Buff.\n"
                    "• Gõ `.help` để xem hướng dẫn."
                ),
                color=discord.Color.green(),
            )
            await channel.send(embed=embed)


@bot.command(name="help")
async def help_cmd(ctx):
    embed = discord.Embed(
        title="📖 BẢNG HƯỚNG DẪN SỬ DỤNG BOT",
        description="Dưới đây là các lệnh khả dụng của Bot Mini World:",
        color=discord.Color.gold(),
    )
    embed.add_field(
        name="👤 Tra cứu người chơi",
        value="Cú pháp: `.check <ID_MINI_WORLD>`\nVí dụ: `.check 322265657`",
        inline=False,
    )
    embed.add_field(
        name="📦 Tra cứu Vật phẩm / Quái / Buff / API Lua",
        value=(
            "Cú pháp: `.find <Tên hoặc ID>`\n"
            "Ví dụ:\n"
            "• `.find 103` (Tra ID)\n"
            "• `.find thiêu đốt` (Tra Buff)\n"
            "• `.find âm ảnh` (Tra Vật phẩm/Buff)\n"
            "• `.find sound` (Tra âm thanh / API)"
        ),
        inline=False,
    )
    embed.add_field(name="❓ Xem hướng dẫn", value="Cú pháp: `.help`", inline=False)
    embed.set_footer(text="Hệ thống tự động tra cứu Mini World")
    await ctx.send(embed=embed)


@bot.command(name="find")
async def find_cmd(ctx, *, query: str = None):
    if not query:
        await ctx.send(
            "❌ Vui lòng nhập từ khóa hoặc ID cần tra cứu. Ví dụ: `.find âm ảnh` hoặc `.find 103`"
        )
        return

    results = mw_db.search(query, limit=5)

    if not results:
        await ctx.send(
            f"❌ Không tìm thấy kết quả nào phù hợp với từ khóa: **{query}**"
        )
        return

    embed = discord.Embed(
        title=f"🔍 KẾT QUẢ TRA CỨU DATABASE: {query}",
        color=discord.Color.purple(),
    )

    for item in results:
        field_name = f"[{item['type']}] {item['name']} (ID: {item['id']})"
        field_value = item["desc"] if item["desc"] else "Không có mô tả."

        if item["type"] == "Lua Script API":
            if item.get("syntax"):
                field_value += f"\n**Cú pháp:** `{item['syntax']}`"
            if item.get("example"):
                field_value += f"\n**Ví dụ:** `{item['example']}`"

        embed.add_field(name=field_name, value=field_value[:1024], inline=False)

    embed.set_footer(text="Cơ sở dữ liệu Mini World CREATA")
    await ctx.send(embed=embed)


@bot.command(name="check")
async def check_cmd(ctx, target_id: str = None):
    if not target_id:
        await ctx.send("❌ Vui lòng nhập ID cần tra cứu. Ví dụ: `.check 322265657`")
        return

    msg = await ctx.send("🔍 Đang tra cứu dữ liệu...")

    t0 = time.time()
    server_uin, server_items, api_url = query_live_server(target_id)
    elapsed = time.time() - t0

    if not server_items:
        await msg.edit(
            content=f"❌ Không tìm thấy dữ liệu cho ID Mini World: **{target_id}**"
        )
        return

    embed = discord.Embed(
        title=f"HỒ SƠ NGƯỜI CHƠI MINI WORLD - ID: {target_id}",
        color=discord.Color.blue(),
    )
    embed.add_field(
        name="🌐 Server UIN",
        value=server_uin if server_uin else target_id,
        inline=True,
    )
    embed.add_field(name="📡 Trạng thái", value="Đang hoạt động", inline=True)

    perm_items = [i for i in server_items if i.get("ExpireTime") == -1]
    temp_items = [i for i in server_items if i.get("ExpireTime") != -1]

    items_str = ""
    for idx, item in enumerate(server_items[:10], 1):
        p_name = get_part_name(item.get("Part", 0))
        m_id = item.get("ModelID", 0)
        exp = format_timestamp(item.get("ExpireTime"))
        items_str += f"**{idx}.** {p_name} | Model: `{m_id}` | Hạn: *{exp}*\n"

    if len(server_items) > 10:
        items_str += f"*...và còn {len(server_items) - 10} món khác.*"

    embed.add_field(
        name=(
            f"📦 Trang phục & Phụ kiện ({len(server_items)} món) - [Vĩnh viễn:"
            f" {len(perm_items)} | Hạn: {len(temp_items)}]"
        ),
        value=items_str,
        inline=False,
    )

    embed.set_footer(text=f"Tốc độ phản hồi: {elapsed:.2f}s")
    await msg.delete()
    await ctx.send(embed=embed)


if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ LỖI: Chưa tìm thấy DISCORD_TOKEN trong Biến môi trường (Environment Variables)!")
