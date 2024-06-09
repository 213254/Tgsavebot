import os
import telebot
from pytube import YouTube
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# Загрузка переменных окружения из .env файла
load_dotenv()

API_TOKEN = os.getenv('TELEGRAM_BOT_API_TOKEN')

bot = telebot.TeleBot(API_TOKEN)

# Создание веб-сервера Flask для поддержания активности
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Отправь мне ссылку на видео с YouTube, и я скачаю его для тебя.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.chat.type in ['group', 'supergroup']:
        if bot.get_me().username in message.text:
            url = message.text.split()[-1]
            process_youtube_link(message, url)
    else:
        process_youtube_link(message, message.text)

def progress_callback(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    progress = (bytes_downloaded / total_size) * 100
    print(f"Загружено: {progress:.1f}%", end='\r')

def process_youtube_link(message, url):
    try:
        yt = YouTube(url, on_progress_callback=progress_callback)
        video = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        video.download(filename='downloaded_video.mp4')

        bot.reply_to(message, "Видео успешно скачано. Отправляю файл...")

        # Отправка файла пользователю
        with open('downloaded_video.mp4', 'rb') as video_file:
            bot.send_video(message.chat.id, video_file)

        # Удаление файла после отправки
        os.remove('downloaded_video.mp4')
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {e}")

if __name__ == '__main__':
    keep_alive()
    bot.polling()