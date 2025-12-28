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

# --- 2. 擴充翻譯對照表 ---
I18N = {
    'en-US': {
        'title': "Jitsi Music Room 🎤",
        'desc': "Room: **{name}**\n\n⚠️ Use **Chrome/Edge** for best audio.",
        'btn_join': "Count me in!",
        'btn_chat': "Chat Only",
        'btn_mono': "Where can I find my right side audio...",
        'btn_custom': "Go to Web Version",
        'footer': "Click the button to join",
        'pro_prompt': "Choose Audio Quality:",
        'q_low': "Survival Mode (96K)",
        'q_mid': "Normal (192K)",
        'q_high': "CD Quality (320K)",
        'q_max': "Net Killer (512K)"
    },
    'zh-TW': {
        'title': "要不要來唱歌 🎤",
        'desc': "房間名稱：**{name}**\n\n⚠️ **提示**：為了確保音質，請使用 **Chrome** 或 **Edge** 瀏覽器開啟。",
        'btn_join': "來了！",
        'btn_chat': "尬聊",
        'btn_mono': "為什麼我聲音只有單邊",
        'btn_custom': "網頁版產生器",
        'footer': "點擊下方按鈕直接進入房間",
        'pro_prompt': "請選擇音質（此訊息僅您可見）：",
        'q_low': "開窗都被嫌從頭卡到尾 (96K)",
        'q_mid': "我只是好奇這個指令是什麼 (192K)",
        'q_high': "CD音質，絕不妥協 (320K)",
        'q_max': "挑戰網速極限 (512K)"
    },
    'ja': {
        'title': "歌おうぜ！ 🎤",
        'desc': "ルーム：**{name}**\n\n⚠️ **Chrome/Edge** 推奨",
        'btn_join': "よっしゃ！",
        'btn_chat': "雑談のみ",
        'btn_mono': "片耳しか聞こえない人用",
        'btn_custom': "ウェブ版",
        'footer': "ボタンを押して入室",
        'pro_prompt': "音質を選んでください：",
        'q_low': "低速回線用 (96K)",
        'q_mid': "標準設定 (192K)",
        'q_high': "ハイレゾ級 (320K)",
        'q_max': "ネットワークの限界へ (512K)"
    }
}

def get_text(locale, key):
    lang = str(locale)
    if lang.startswith('zh'): lang = 'zh-TW'
    elif lang.startswith('ja'): lang = 'ja'
    else: lang = 'en-US'
    return I18N.get(lang, I18N['en-US'])[key]

# --- 3. Jitsi 網址生成邏輯 ---
def get_jitsi_url(room_name, mode, bitrate=192000):
    encoded_name = urllib.parse.quote(room_name)
    # mode: 'stereo', 'mono', 'chat'
    is_stereo = "true" if mode in ['stereo', 'chat'] else "false"
    # 尬聊模式開啟音訊處理 (disableAP=false)
    disable_ap = "false" if mode == 'chat' else "true"
    
    config = (f"config.disableAP={disable_ap}&config.disableAEC={disable_ap}&"
              f"config.disableNS={disable_ap}&config.disableAGC={disable_ap}&"
              f"config.stereo={is_stereo}&"
              f"config.opusMaxAverageBitrate={bitrate}&"
              f"config.startWithAudioMuted=true&config.startWithVideoMuted=true")
    return f"https://meet.jit.si/{encoded_name}#{config}"

# --- 4. 互動組件 ---
class ProQualitySelect(ui.View):
    def __init__(self, room_name, locale):
        super().__init__(timeout=60)
        self.room_name = room_name
        self.locale = locale

    async def send_public_room(self, interaction: discord.Interaction, br, br_label):
        embed = discord.Embed(
            title=get_text(self.locale, 'title'),
            description=get_text(self.locale, 'desc').format(name=self.room_name, br=br_label),
            color=0x4687ed
        )
        embed.set_footer(text=get_text(self.locale, 'footer'))
        
        view = ui.View()
        view.add_item(ui.Button(label=get_text(self.locale, 'btn_join'), style=discord.ButtonStyle.primary, url=get_jitsi_url(self.room_name, 'stereo', br), emoji="✊"))
        view.add_item(ui.Button(label=get_text(self.locale, 'btn_chat'), style=discord.ButtonStyle.success, url=get_jitsi_url(self.room_name, 'chat', br), emoji="💬"))
        view.add_item(ui.Button(label=get_text(self.locale, 'btn_mono'), style=discord.ButtonStyle.gray, url=get_jitsi_url(self.room_name, 'mono', br), emoji="♿"))
        view.add_item(ui.Button(label=get_text(self.locale, 'btn_custom'), style=discord.ButtonStyle.link, url="https://szyln.github.io/jitsi-for-music-url-generator/", emoji="⚙️"))
        
        # 刪除暫時的 Ephemeral 訊息並發送公開訊息
        await interaction.response.edit_message(content="✅ Room link sent!", view=None)
        await interaction.channel.send(embed=embed, view=view)

    @ui.button(label="96K", style=discord.ButtonStyle.secondary)
    async def q_low(self, interaction: discord.Interaction, button: ui.Button):
        await self.send_public_room(interaction, 96000, get_text(self.locale, 'q_low'))

    @ui.button(label="192K", style=discord.ButtonStyle.secondary)
    async def q_mid(self, interaction: discord.Interaction, button: ui.Button):
        await self.send_public_room(interaction, 192000, get_text(self.locale, 'q_mid'))

    @ui.button(label="320K", style=discord.ButtonStyle.secondary)
    async def q_high(self, interaction: discord.Interaction, button: ui.Button):
        await self.send_public_room(interaction, 320000, get_text(self.locale, 'q_high'))

    @ui.button(label="512K", style=discord.ButtonStyle.danger)
    async def q_max(self, interaction: discord.Interaction, button: ui.Button):
        await self.send_public_room(interaction, 512000, get_text(self.locale, 'q_max'))

# --- 5. 機器人主體 ---
class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)
    async def setup_hook(self): await self.tree.sync()

client = MyBot()

@client.tree.command(name="jitsi", description="Quickly generate a 192K Jitsi room")
async def jitsi(interaction: discord.Interaction, room_name: str):
    user_locale = interaction.locale
    embed = discord.Embed(
        title=get_text(user_locale, 'title'),
        description=get_text(user_locale, 'desc').format(name=room_name, br="192K"),
        color=0x4687ed
    )
    view = ui.View()
    view.add_item(ui.Button(label=get_text(user_locale, 'btn_join'), style=discord.ButtonStyle.primary, url=get_jitsi_url(room_name, 'stereo'), emoji="✊"))
    view.add_item(ui.Button(label=get_text(user_locale, 'btn_chat'), style=discord.ButtonStyle.success, url=get_jitsi_url(room_name, 'chat'), emoji="💬"))
    view.add_item(ui.Button(label=get_text(user_locale, 'btn_mono'), style=discord.ButtonStyle.gray, url=get_jitsi_url(room_name, 'mono'), emoji="♿"))
    await interaction.response.send_message(embed=embed, view=view)

@client.tree.command(name="jitsi_pro", description="Generate a room with custom quality")
async def jitsi_pro(interaction: discord.Interaction, room_name: str):
    user_locale = interaction.locale
    # 使用 ephemeral=True 讓選單只有指令者看得到
    await interaction.response.send_message(
        content=f"**{room_name}** - {get_text(user_locale, 'pro_prompt')}",
        view=ProQualitySelect(room_name, user_locale),
        ephemeral=True
    )

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.environ.get('BOT_TOKEN')
    if TOKEN: client.run(TOKEN)