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
    # 根據 Render 日誌，確保使用正確的 Port 
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run_flask).start()

# --- 2. 翻譯對照表 (精簡合併版) ---
I18N = {
    'en-US': {
        'title': "Jitsi Music Room 🎤",
        'desc': "Room: **{name}**\n\n⚠️ Use **Chrome/Edge** for best audio.",
        'btn_join': "Count me in!",
        'btn_mono': "Click me if your sound is only in one side",
        'footer': "Select a mode to join"
    },
    'zh-TW': {
        'title': "要不要來唱歌 🎤",
        'desc': "房間名稱：**{name}**\n\n⚠️ **提示**：為了確保音質，請使用 **Chrome** 或 **Edge** 瀏覽器開啟。",
        'btn_join': "來了！",
        'btn_mono': "為什麼我聲音只有單邊",
        'footer': "點擊下方按鈕直接進入房間"
    },
    'ja': {
        'title': "歌おうぜ！ 🎤",
        'desc': "ルーム：**{name}**\n\n⚠️ **Chrome/Edge** 推奨",
        'btn_join': "よっしゃ！",
        'btn_mono': "片耳しか聞こえない人用",
        'footer': "ボタンを押して入室"
    }
}

def get_text(locale, key):
    lang = str(locale)
    if lang.startswith('zh'): lang = 'zh-TW'
    elif lang.startswith('ja'): lang = 'ja'
    else: lang = 'en-US'
    return I18N.get(lang, I18N['en-US'])[key]

# --- 3. Jitsi 網址生成邏輯 (已合併設定) ---
def get_jitsi_url(room_name, mode):
    encoded_name = urllib.parse.quote(room_name)
    # 預設參數：高音質、開啟立體聲、預設關閉視訊
    ap, s, ma, mv, br = "true", "true", "true", "true", "128000"
    
    if mode == 'compat':
        s = "false" # 單聲道模式關閉立體聲
        ma = "false" # 相容模式預設開啟麥克風以利測試
    
    config = (f"config.disableAP={ap}&config.disableAEC={ap}&config.disableNS={ap}&"
              f"config.disableAGC={ap}&config.stereo={s}&"
              f"config.opusMaxAverageBitrate={br}&"
              f"config.startWithAudioMuted={ma}&config.startWithVideoMuted={mv}")
    return f"https://meet.jit.si/{encoded_name}#{config}"

# --- 4. 按鈕視圖類別 (兩個按鈕) ---
class JitsiButtons(ui.View):
    def __init__(self, room_name, locale):
        super().__init__()
        # 合併後的進場按鈕 (預設關麥)
        self.add_item(ui.Button(
            label=get_text(locale, 'btn_join'), 
            style=discord.ButtonStyle.primary, 
            url=get_jitsi_url(room_name, 'join'),
            emoji="✊"
        ))
        # 單聲道相容按鈕
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

@client.event
async def on_ready():
    # 確保在 Render 啟動後強制同步指令 
    print(f'機器人已上線：{client.user}')
    try:
        synced = await client.tree.sync()
        print(f"成功同步了 {len(synced)} 個指令")
    except Exception as e:
        print(f"同步指令失敗: {e}")

@client.tree.command(name="jitsi", description="Generate optimized Jitsi links")
@app_commands.describe(room_name="Enter the room name")
async def jitsi(interaction: discord.Interaction, room_name: str):
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
    # 1. 先啟動 Flask
    print(">>> 正在啟動 Flask 背景服務...")
    keep_alive()
    
    # 2. 檢查環境變數
    TOKEN = os.environ.get('BOT_TOKEN')
    
    if not TOKEN:
        print("❌ 錯誤：在 Render 環境變數中找不到 'BOT_TOKEN'！")
        print("請檢查 Render Dashboard -> Environment -> Add Environment Variable")
    else:
        print(f"✅ 成功讀取 TOKEN (長度: {len(TOKEN)})，正在嘗試連線至 Discord...")
        try:
            # 3. 啟動機器人 (這行必須是最後一行，因為它會阻塞程式運行)
            client.run(TOKEN)
        except discord.errors.LoginFailure:
            print("❌ 錯誤：Token 無效，請重新從 Discord Developer Portal 複製。")
        except Exception as e:
            print(f"❌ 啟動時發生未預期錯誤: {e}")