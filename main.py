import discord
from discord import app_commands, ui
import urllib.parse
import os
from flask import Flask
from threading import Thread

# --- 1. 防止休眠伺服器 (沿用) ---
app = Flask('')
@app.route('/')
def home(): return "Jitsi Bot with Buttons is Online!"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run_flask).start()

# --- 2. Jitsi 網址生成邏輯 (沿用) ---
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

# --- 3. 按鈕視圖類別 ---
class JitsiButtons(ui.View):
    def __init__(self, room_name):
        super().__init__()
        # 加入音樂模式按鈕
        self.add_item(ui.Button(
            label="音樂模式", 
            style=discord.ButtonStyle.primary, 
            url=get_jitsi_url(room_name, 'music'),
            emoji="🎵"
        ))
        # 加入觀眾模式按鈕
        self.add_item(ui.Button(
            label="觀眾模式", 
            style=discord.ButtonStyle.secondary, 
            url=get_jitsi_url(room_name, 'audience'),
            emoji="🎧"
        ))
        # 加入單聲道模式按鈕
        self.add_item(ui.Button(
            label="單聲道模式", 
            style=discord.ButtonStyle.gray, 
            url=get_jitsi_url(room_name, 'compat'),
            emoji="📻"
        ))

# --- 4. 機器人主體 ---
class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

client = MyBot()

@client.tree.command(name="jitsi", description="生成音樂優化的 Jitsi 按鈕連結")
async def jitsi(interaction: discord.Interaction, room_name: str):
    # 建立一個 Embed 讓外觀更專業
    embed = discord.Embed(
        title=f"🎸 Jitsi 房間準備就緒",
        description=f"房間名稱：**{room_name}**\n\n⚠️ **提示**：為了確保音質，請使用 **Chrome** 或 **Edge** 瀏覽器開啟。",
        color=0x4687ed
    )
    embed.set_footer(text="點擊下方按鈕直接進入房間")
    
    # 送出訊息，並帶上按鈕組
    await interaction.response.send_message(embed=embed, view=JitsiButtons(room_name))

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.environ.get('BOT_TOKEN')
    if TOKEN: client.run(TOKEN)