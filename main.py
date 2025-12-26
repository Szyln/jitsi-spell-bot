import discord
from discord import app_commands, ui
import urllib.parse
import os
from flask import Flask
from threading import Thread

# --- 1. 防止休眠伺服器 ---
app = Flask('')
@app.route('/')
def home(): return "Multilingual Jitsi Bot is Online!"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run_flask).start()

# --- 2. 翻譯對照表 (中文原版 / 英日極簡版) ---
I18N = {
    'en-US': {
        'title': "Jitsi Music Room 🎤",
        'desc': "Room: **{name}**\n\n⚠️ Use **Chrome/Edge** for best audio.",
        'btn_music': "I'll sing",
        'btn_audience': "Just listen",
        'btn_mono': "Click me if your sound is only in one side ",
        'footer': "Select a mode to join"
    },
    'zh-TW': {
        'title': "要不要來唱歌 🎤",
        'desc': "房間名稱：**{name}**\n\n⚠️ **提示**：為了確保音質，請使用 **Chrome** 或 **Edge** 瀏覽器開啟。",
        'btn_music': "我也要唱",
        'btn_audience': "我只想聽",
        'btn_mono': "為什麼我聲音只有單邊",
        'footer': "點擊下方按鈕直接進入房間"
    },
    'ja': {
        'title': "歌おうぜ！ 🎤",
        'desc': "ルーム：**{name}**\n\n⚠️ **Chrome/Edge** 推奨",
        'btn_music': "よっしゃ",
        'btn_audience': "聞き専",
        'btn_mono': "片耳しか出せない人用",
        'footer': "ボタンを押して入室"
    }
}


def get_text(locale, key):
    # Discord 的繁中代碼可能是 zh-TW，也可能是 zh-CN，這裡簡化處理
    lang = str(locale)
    if lang.startswith('zh'): lang = 'zh-TW'
    elif lang.startswith('ja'): lang = 'ja'
    else: lang = 'en-US' # 預設英文
    
    return I18N.get(lang, I18N['en-US'])[key]

# --- 3. Jitsi 網址生成邏輯 (保持不變) ---
def get_jitsi_url(room_name, mode):
    encoded_name = urllib.parse.quote(room_name)
    ap, s, ma, mv, br = "true", "true", "false", "true", "128000"
    if mode == 'music': s, ma = "true", "false"
    elif mode == 'audience': s, ma = "true", "true"
    elif mode == 'compat': s, ma = "false", "false"
    
    config = (f"config.disableAP={ap}&config.disableAEC={ap}&config.disableNS={ap}&"
              f"config.disableAGC={ap}&config.stereo={s}&"
              f"config.opusMaxAverageBitrate={br}&"
              f"config.startWithAudioMuted={ma}&config.startWithVideoMuted={mv}")
    return f"https://meet.jit.si/{encoded_name}#{config}"

# --- 4. 按鈕視圖類別 (帶入語言) ---
class JitsiButtons(ui.View):
    def __init__(self, room_name, locale):
        super().__init__()
        self.add_item(ui.Button(
            label=get_text(locale, 'btn_music'), 
            style=discord.ButtonStyle.primary, 
            url=get_jitsi_url(room_name, 'music'),
            emoji="🎤"
        ))
        self.add_item(ui.Button(
            label=get_text(locale, 'btn_audience'), 
            style=discord.ButtonStyle.secondary, 
            url=get_jitsi_url(room_name, 'audience'),
            emoji="🎧"
        ))
        self.add_item(ui.Button(
            label=get_text(locale, 'btn_mono'), 
            style=discord.ButtonStyle.gray, 
            url=get_jitsi_url(room_name, 'compat'),
            emoji="❓"
        ))

# --- 5. 機器人主體 ---
class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)
    async def setup_hook(self):
        await self.tree.sync()

client = MyBot()

@client.tree.command(name="jitsi", description="Generate optimized Jitsi links")
@app_commands.describe(room_name="Enter the room name")
async def jitsi(interaction: discord.Interaction, room_name: str):
    # 獲取用戶語言
    user_locale = interaction.locale
    
    embed = discord.Embed(
        title=get_text(user_locale, 'title'),
        description=get_text(user_locale, 'desc').format(name=room_name),
        color=0x4687ed
    )
    embed.set_footer(text=get_text(user_locale, 'footer'))
    
    await interaction.response.send_message(
        embed=embed, 
        view=JitsiButtons(room_name, user_locale)
    )

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.environ.get('BOT_TOKEN')
    if TOKEN: client.run(TOKEN)
