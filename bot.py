import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import subprocess

BOT_TOKEN = "7809603810:AAG9KGu5eramPitX24ECZ4r92_RGmpl3dA4"
bot = telebot.TeleBot(BOT_TOKEN)

CHANNELS = {
    "J-ONE": "@japon_one1",
    "J-ONE 🇫🇷": "@japon_one1VF",
    "MOVIE BOX": "@movieboxfr",
}

def check_subscription(user_id):
    for channel_name, channel_username in CHANNELS.items():
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
        markup.add(InlineKeyboardButton(text=f"S'abonner à {channel_name}", url=f"https://t.me/{channel_username[1:]}"))
    return markup

def progress_bar(downloaded, total, speed, eta):
    percent = int((downloaded / total) * 100)
    bar_length = 20
    completed = int((percent / 100) * bar_length)
    remaining = bar_length - completed

    bar = f"{'█' * completed}{'░' * remaining}"
    progress = (
        f"Résultats obtenus\n"
        f"@japon_one1 le meilleur canal de tous les temps....\n\n"
        f"{bar}\n\n"
        f"╭━━━━❰ᴘʀᴏɢʀᴇss ʙᴀʀ❱━➣\n"
        f"┣⪼ 🗂️ : {downloaded / (1024 * 1024):.2f} MB | {total / (1024 * 1024):.2f} MB\n"
        f"┣⪼ ⏳️ : {percent}%\n"
        f"┣⪼ 🚀 : {speed / (1024 * 1024):.2f} MB/s\n"
        f"┣⪼ ⏱️ : {eta:.2f} s\n"
        f"╰━━━━━━━━━━━━━━━➣"
    )
    return progress

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
        bot.reply_to(message, "Veuillez envoyer un lien valide.")
        return

    chat_id = message.chat.id
    progress_message = bot.send_message(chat_id, "Initialisation du téléchargement...")

    try:
        def hook(d):
            if d['status'] == 'downloading':
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes', 1)
                speed = d.get('speed', 0)
                eta = d.get('eta', 0)

                progress_text = progress_bar(downloaded, total, speed, eta)
                bot.edit_message_text(progress_text, chat_id, progress_message.message_id)

        ydl_opts = {
            'outtmpl': 'video.%(ext)s',
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
            'merge_output_format': 'mp4',
            'quiet': True,
            'progress_hooks': [hook],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_title = info.get('title', 'video')

        # Vérifie si la vidéo dépasse 50 MB
        if os.path.exists("video.mp4") and os.path.getsize("video.mp4") > 50 * 1024 * 1024:
            bot.send_message(chat_id, "Compression en cours (vidéo > 50MB)...")
            subprocess.run([
                "ffmpeg", "-i", "video.mp4",
                "-vcodec", "libx264", "-crf", "28",
                "compressed.mp4"
            ])
            os.remove("video.mp4")
            os.rename("compressed.mp4", "video.mp4")

        with open("video.mp4", "rb") as video_file:
            bot.send_video(chat_id, video_file, caption=f"Titre : {video_title}")

        os.remove("video.mp4")

    except Exception as e:
        bot.edit_message_text(
            "Erreur lors de l'extraction ou du téléchargement :\n\n"
            "Veuillez vérifier le lien et réessayer.",
            chat_id,
            progress_message.message_id
        )

bot.infinity_polling()
