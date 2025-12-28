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
        'desc': "Room: **{name}**\nQuality: **{br}**\n\n⚠️ Use **Chrome/Edge** for best audio.",
        'btn_join': "Count me in!",
        'btn_chat': "Chat Only",
        'btn_mono': "Mono Audio Fix",
        'footer': "Click the button to join",
        'pro_prompt': "Choose Audio Quality:",
        'pro_done': "✅ Room link generated!",
        'q_low': "Survival Mode (96K)",
        'q_mid': "Just curious about this (192K)",
        'q_high': "CD Quality, no compromise (320K)",
        'q_max': "Testing network limits (512K)"
    },
    'zh-TW': {
        'title': "要不要來唱歌 🎤",
        'desc': "房間名稱：**{name}**\n音質：**{br}**\n\n⚠️ **提示**：為了確保音質，請使用 **Chrome** 或 **Edge** 瀏覽器開啟。",
        'btn_join': "來了！",
        'btn_chat': "尬聊",
        'btn_mono': "為什麼我聲音只有單邊",
        'footer': "點擊下方按鈕直接進入房間",
        'pro_prompt': "請選擇音質：",
        'pro_done': "✅ 房間連結已產生！",
        'q_low': "只求連上，不求音質 (96K)",
        'q_mid': "我只是好奇這個指令是什麼 (192K)",
        'q_high': "CD音質，絕不妥協 (320K)",
        'q_max': "挑戰網速極限 (512K)"
    },
    'ja': {
        'title': "歌おうぜ！ 🎤",
        'desc': "ルーム：**{name}**\n音質：**{br}**\n\n⚠️ **Chrome/Edge** 推奨",
        'btn_join': "よっしゃ！",
        'btn_chat': "雑談のみ",
        'btn_mono': "片耳しか聞こえない人用",
        'footer': "ボタンを押して入室",
        'pro_prompt': "音質を選んでください：",
        'pro_done': "✅ ルームURLを作成しました！",
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
    is_stereo = "true" if mode in ['stereo', 'chat'] else "false"
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
        
        # 本人看到的選單按鈕顯示完整趣味說明
        self.btn_q_low.label = get_text(locale, 'q_low')
        self.btn_q_mid.label = get_text(locale, 'q_mid')
        self.btn_q_high.label = get_text(locale, 'q_high')
        self.btn_q_max.label = get_text(locale, 'q_max')

    async def send_public_room(self, interaction: discord.Interaction, br, br_label):
        embed = discord.Embed(
            title=get_text(self.locale, 'title'),
            # 此處的 br 使用簡潔的標籤 (例如 "96K")
            description=get_text(self.locale, 'desc').format(name=self.room_name, br=br_label),
            color=0x4687ed
        )
        embed.set_footer(text=get_text(self.locale, 'footer'))
        
        view = ui.View()
        view.add_item(ui.Button(label=get_text(self.locale, 'btn_join'), style=discord.ButtonStyle.primary, url=get_jitsi_url(self.room_name, 'stereo', br), emoji="✊"))
        view.add_item(ui.Button(label=get_text(self.locale, 'btn_chat'), style=discord.ButtonStyle.success, url=get_jitsi_url(self.room_name, 'chat', br), emoji="📢"))
        view.add_item(ui.Button(label=get_text(self.locale, 'btn_mono'), style=discord.ButtonStyle.gray, url=get_jitsi_url(self.room_name, 'mono', br), emoji="♿"))
        
        await interaction.response.edit_message(content=get_text(self.locale, 'pro_done'), view=None)
        await interaction.channel.send(embed=embed, view=view)

    @ui.button(style=discord.ButtonStyle.secondary)
    async def btn_q_low(self, interaction: discord.Interaction, button: ui.Button):
        # 公開訊息顯示簡潔標籤
        await self.send_public_room(interaction, 96000, "96K")

    @ui.button(style=discord.ButtonStyle.secondary)
    async def btn_q_mid(self, interaction: discord.Interaction, button: ui.Button):
        await self.send_public_room(interaction, 192000, "192K")

    @ui.button(style=discord.ButtonStyle.secondary)
    async def btn_q_high(self, interaction: discord.Interaction, button: ui.Button):
        await self.send_public_room(interaction, 320000, "320K")

    @ui.button(style=discord.ButtonStyle.danger)
    async def btn_q_max(self, interaction: discord.Interaction, button: ui.Button):
        await self.send_public_room(interaction, 512000, "512K")

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
    view.add_item(ui.Button(label=get_text(user_locale, 'btn_chat'), style=discord.ButtonStyle.success, url=get_jitsi_url(room_name, 'chat'), emoji="📢"))
    view.add_item(ui.Button(label=get_text(user_locale, 'btn_mono'), style=discord.ButtonStyle.gray, url=get_jitsi_url(room_name, 'mono'), emoji="♿"))
    await interaction.response.send_message(embed=embed, view=view)

@client.tree.command(name="jitsi_pro", description="Generate a room with custom quality")
async def jitsi_pro(interaction: discord.Interaction, room_name: str):
    user_locale = interaction.locale
    await interaction.response.send_message(
        content=f"**{room_name}** - {get_text(user_locale, 'pro_prompt')}",
        view=ProQualitySelect(room_name, user_locale),
        ephemeral=True
    )

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.environ.get('BOT_TOKEN')
    if TOKEN: client.run(TOKEN)