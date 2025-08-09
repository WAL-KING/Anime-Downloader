import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import subprocess

BOT_TOKEN = "7809603810:AAF3xUiYFEd93U1UAillmIb-Zp9b03ICCm0"
CHANNELS = {
    "J-ONE 🇫🇷": "@japonone",
}
bot = telebot.TeleBot(BOT_TOKEN)

def check_subscription(user_id):
    for _, channel_username in CHANNELS.items():
        try:
            status = bot.get_chat_member(channel_username, user_id).status
            if status not in ("member", "administrator", "creator"):
                return False
        except Exception:
            return False
    return True

def subscription_buttons():
    markup = InlineKeyboardMarkup()
    for channel_name, channel_username in CHANNELS.items():
        markup.add(InlineKeyboardButton(
            text=f"S'abonner à {channel_name}",
            url=f"https://t.me/{channel_username[1:]}"
        ))
    return markup

def progress_bar(downloaded, total, speed, eta):
    """Affiche une barre de progression textuelle."""
    percent = int((downloaded / total) * 100) if total > 0 else 0
    bar_length = 20
    completed = int((percent / 100) * bar_length)
    remaining = bar_length - completed
    bar = f"{'█' * completed}{'░' * remaining}"

    return (
        f"Résultats obtenus\nMerci de nous faire confiance....\n\n"
        f"{bar}\n\n"
        f"╭━━━━❰ᴘʀᴏɢʀᴇss ʙᴀʀ❱━➣\n"
        f"┣⪼ 🗂️ : {downloaded / (1024 * 1024):.2f} MB | {total / (1024 * 1024):.2f} MB\n"
        f"┣⪼ ⏳️ : {percent}%\n"
        f"┣⪼ 🚀 : {speed / (1024 * 1024):.2f} MB/s\n"
        f"┣⪼ ⏱️ : {eta:.2f} s\n"
        f"╰━━━━━━━━━━━━━━━➣"
    )

@bot.message_handler(commands=['start'])
def start(message):
    if not check_subscription(message.from_user.id):
        bot.send_message(
            message.chat.id,
            "Pour utiliser ce bot, veuillez d'abord vous abonner aux chaînes suivantes :",
            reply_markup=subscription_buttons(),
        )
    else:
        bot.reply_to(message, "Envoyez-moi un lien de streaming vidéo, et je tenterai de le télécharger.")

@bot.message_handler(func=lambda message: True)
def download_video(message):
    if not check_subscription(message.from_user.id):
        bot.send_message(
            message.chat.id,
            "Pour utiliser ce bot, veuillez d'abord vous abonner aux chaînes suivantes :",
            reply_markup=subscription_buttons(),
        )
        return

    url = message.text.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        bot.reply_to(message, "❌ Veuillez envoyer un lien valide.")
        return

    chat_id = message.chat.id
    progress_message = bot.send_message(chat_id, "📥 Initialisation du téléchargement...")

    try:
        def hook(d):
            if d['status'] == 'downloading':
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes', 1)
                speed = d.get('speed', 0) or 0
                eta = d.get('eta', 0)
                bot.edit_message_text(
                    progress_bar(downloaded, total, speed, eta),
                    chat_id,
                    progress_message.message_id
                )

        ydl_opts = {
            'outtmpl': 'video.%(ext)s',
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
            'merge_output_format': 'mp4',
            'progress_hooks': [hook],
            'quiet': True,
            'retries': float('inf'),       
            'fragment_retries': 100,       
            'continuedl': True,            
            'socket_timeout': 60,         
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_title = info.get('title', 'video')

        # Envoi direct de la vidéo
        if os.path.exists("video.mp4"):
            with open("video.mp4", "rb") as video_file:
                bot.send_video(chat_id, video_file, caption=f"🎬 {video_title}")

    except Exception as e:
        bot.edit_message_text(
            f"❌ Erreur lors du téléchargement : {e}",
            chat_id,
            progress_message.message_id
        )

    finally:
        # Nettoyage
        if os.path.exists("video.mp4"):
            os.remove("video.mp4")

print("✅ Bot en ligne")
bot.infinity_polling()