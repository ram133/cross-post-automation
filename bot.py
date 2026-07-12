
import os
import logging
import asyncio
import json
from telegram import Update, Bot
from telegram.ext import Application

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
STATE_FILE = "last_update_id.txt"

# List of other bot tokens for cross-posting
OTHER_BOT_TOKENS = [
    "8056349243:AAH7CVgBx5_ese73xjCg3ah71T6-NlrOeaI",  # @RAY2FBbot
    "7355656881:AAEe3hHYjDAlg6aVQ8Iw8M125qxqBxlnYK4"   # @My0724bot
]

def get_last_update_id():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try:
                return int(f.read().strip())
            except ValueError:
                return 0
    return 0

def save_last_update_id(update_id):
    with open(STATE_FILE, "w") as f:
        f.write(str(update_id))

async def post_to_telegram_bots(text: str, photo_path: str = None, video_path: str = None) -> None:
    """Cross-post to other Telegram bots."""
    if not TELEGRAM_CHAT_ID:
        logger.error("TELEGRAM_CHAT_ID environment variable not set for cross-posting.")
        return

    for token in OTHER_BOT_TOKENS:
        try:
            bot = Bot(token=token)
            if photo_path:
                with open(photo_path, 'rb') as photo_file:
                    await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=photo_file, caption=text)
            elif video_path:
                with open(video_path, 'rb') as video_file:
                    await bot.send_video(chat_id=TELEGRAM_CHAT_ID, video=video_file, caption=text)
            else:
                await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)
            logger.info(f"Successfully cross-posted to bot with token: {token[:5]}...")
        except Exception as e:
            logger.error(f"Error cross-posting to bot with token {token[:5]}...: {e}")

async def process_update(bot: Bot, update: Update):
    """Process a single update."""
    if not update.message:
        return
    
    # Only process messages from the specific user
    if str(update.message.chat_id) != TELEGRAM_CHAT_ID:
        logger.info(f"Skipping message from unknown chat ID: {update.message.chat_id}")
        return

    message = update.message
    caption = message.caption if message.caption else ""
    file_path = None

    try:
        if message.photo:
            file_id = message.photo[-1].file_id
            file_path = f"{file_id}.jpg"
            file = await bot.get_file(file_id)
            await file.download_to_drive(file_path)
            logger.info(f"Downloaded photo: {file_path}")
            await post_to_telegram_bots(caption, photo_path=file_path)
        elif message.video:
            file_id = message.video.file_id
            file_path = f"{file_id}.mp4"
            file = await bot.get_file(file_id)
            await file.download_to_drive(file_path)
            logger.info(f"Downloaded video: {file_path}")
            await post_to_telegram_bots(caption, video_path=file_path)
        elif message.text:
            text = message.text
            logger.info(f"Received text: {text}")
            await post_to_telegram_bots(text)
        
        # Clean up downloaded file
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up file: {file_path}")
            
    except Exception as e:
        logger.error(f"Error processing update {update.update_id}: {e}")

async def main():
    """Poll for updates and process them."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set.")
        return

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    last_update_id = get_last_update_id()
    
    logger.info(f"Checking for updates starting from {last_update_id + 1}")
    
    updates = await bot.get_updates(offset=last_update_id + 1)
    
    for update in updates:
        await process_update(bot, update)
        last_update_id = update.update_id
        save_last_update_id(last_update_id)

    if not updates:
        logger.info("No new updates found.")

if __name__ == "__main__":
    asyncio.run(main())
