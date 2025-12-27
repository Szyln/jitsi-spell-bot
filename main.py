import discord
from discord import app_commands, ui
import urllib.parse
import os
from flask import Flask
from threading import Thread

# --- 1. 防止休眠伺服器 ---
app = Flask('')
@app.route('/')
def home(): return "Jitsi Bot is Online!"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run_flask).start()

# --- 2. 翻譯對照表 ---
I18N = {
    'en-US': {
        'title': "Jitsi Music Room 🎤",
        'desc': "Room: **{name}**\n\n⚠️ Use **Chrome/Edge** for best audio.",
        'btn_join': "Count me in!",
        'btn_mono': "Why is my sound only on one side",
        'btn_custom': "Custom Settings",
        'footer': "Click the button to join"
    },
    'zh-TW': {
        'title': "要不要來唱歌 🎤",
        'desc': "房間名稱：**{name}**\n\n⚠️ **提示**：為了確保音質，請使用 **Chrome** 或 **Edge** 瀏覽器開啟。",
        'btn_join': "來了！",
        'btn_mono': "為什麼我聲音只有單邊",
        'btn_custom': "自訂",
        'footer': "點擊下方按鈕直接進入房間"
    },
    'ja': {
        'title': "歌おうぜ！ 🎤",
        'desc': "ルーム：**{name}**\n\n⚠️ **Chrome/Edge** 推奨",
        'btn_join': "よっしゃ！",
        'btn_mono': "片耳しか聞こえない人用",
        'btn_custom': "カスタム設定",
        'footer': "ボタンを押して入室"
    }
}

def get_text(locale, key):
    lang = str(locale)
    if lang.startswith('zh'): lang = 'zh-TW'
    elif lang.startswith('ja'): lang = 'ja'
    else: lang = 'en-US'
    return I18N.get(lang, I18N['en-US'])[key]

# --- 3. Jitsi 網址生成邏輯 (預設 192K) ---
def get_jitsi_url(room_name, is_stereo):
    encoded_name = urllib.parse.quote(room_name)
    # 預設參數與網頁版同步
    config = (f"config.disableAP=true&config.disableAEC=true&config.disableNS=true&"
              f"config.disableAGC=true&config.stereo={'true' if is_stereo else 'false'}&"
              f"config.opusMaxAverageBitrate=192000&"
              f"config.startWithAudioMuted=true&config.startWithVideoMuted=true")
    return f"https://meet.jit.si/{encoded_name}#{config}"

# --- 4. 機器人主體 ---
class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

client = MyBot()

@client.event
async def on_ready():
    print(f'✅ 機器人已上線：{client.user}')

@client.tree.command(name="jitsi", description="Generate Jitsi music room links")
@app_commands.describe(room_name="Enter room name")
async def jitsi(interaction: discord.Interaction, room_name: str = None):
    user_locale = interaction.locale
    embed = discord.Embed(
        title=get_text(user_locale, 'title'),
        description=get_text(user_locale, 'desc').format(name=room_name),
        color=0x4687ed
    )
    embed.set_footer(text=get_text(user_locale, 'footer'))
    
    # 建立按鈕視圖
    view = ui.View()
    
    # 1. 來了！ (192K Stereo)
    view.add_item(ui.Button(
        label=get_text(user_locale, 'btn_join'),
        style=discord.ButtonStyle.primary,
        url=get_jitsi_url(room_name, True),
        emoji="✊"
    ))
    
    # 2. 單邊 (192K Mono)
    view.add_item(ui.Button(
        label=get_text(user_locale, 'btn_mono'),
        style=discord.ButtonStyle.gray,
        url=get_jitsi_url(room_name, False),
        emoji="♿"
    ))
    
    # 3. 自訂 (外部連結)
    view.add_item(ui.Button(
        label=get_text(user_locale, 'btn_custom'),
        style=discord.ButtonStyle.link,
        url="https://szyln.github.io/jitsi-for-music-url-generator/",
        emoji="⚙️"
    ))
    
    await interaction.response.send_message(embed=embed, view=view)

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.environ.get('BOT_TOKEN')
    if TOKEN:
        client.run(TOKEN)