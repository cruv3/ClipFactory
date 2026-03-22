import asyncio
import os
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler
from telegram.request import HTTPXRequest
import subprocess

from utils import StoryStrategy
from config import (
    TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
)

class TelegramApproval:
    def __init__(self):
        t_request = HTTPXRequest(connect_timeout=20, read_timeout=300)
        self.bot = Bot(token=TELEGRAM_TOKEN, request=t_request)
        
        self.decision = None
        self.event = asyncio.Event()
        self.last_message_id = None

    async def send_video_for_approval(self, video_path, strategy):
        await asyncio.sleep(2)
        
        preview_path = self._create_preview(video_path)

        strategy_details = (
            f"🎬 <b>AI STRATEGY ANALYSIS</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🗣 <b>Voice:</b> <code>{strategy.voice}</code>\n"
            f"🎯 <b>Hook:</b> {strategy.hook_style}\n"
            f"📁 <b>Category:</b> #{strategy.folder_name}\n\n"
            f"📝 <b>Caption:</b>\n<i>{strategy.caption}</i>\n\n"
            f"📖 <b>Description:</b>\n<i>{strategy.description}</i>\n\n"
            f"🏷 <b>Tags:</b>\n{strategy.tags}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )

        keyboard = [
            [
                InlineKeyboardButton("✅ Upload", callback_data="approve"),
                InlineKeyboardButton("❌ Abort", callback_data="abort"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            print(f"[*] Sending video & strategy to Telegram...")
            with open(preview_path, 'rb') as video_file:
                message = await self.bot.send_video(
                    chat_id=TELEGRAM_CHAT_ID,
                    video=video_file, # Hier das Datei-Objekt übergeben
                    caption=strategy_details,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    write_timeout=600, # Mehr Zeit für große Videos
                    read_timeout=600,
                    connect_timeout=600
                )
                self.last_message_id = message.message_id

                if preview_path != video_path and os.path.exists(preview_path):
                    os.remove(preview_path)
                    
                return message.message_id
        except Exception as e:
            print(f"[!] Telegram Upload Error: {e}")

    def _create_preview(self, video_path):
        preview_path = video_path.replace(".mp4", "_preview.mp4")
        print(f"[*] Creating 20s preview for Telegram...")
        
        cmd = [
            'ffmpeg', '-y', '-i', video_path,
            '-ss', '0', '-t', '20',
            '-vf', 'scale=-1:480',
            '-c:v', 'libx264', '-crf', '28', '-preset', 'veryfast',
            '-c:a', 'aac', '-b:a', '128k',
            preview_path
        ]
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return preview_path
        except Exception as e:
            print(f"[!] Preview Creation Error: {e}")
            return video_path
    
    async def wait_for_approval(self, timeout=1800):
        self.event.clear()
        self.decision = None

        application = Application.builder().token(TELEGRAM_TOKEN).build()
        application.add_handler(CallbackQueryHandler(self._handle_callback))
        
        await application.initialize()
        await application.start()
        await application.updater.start_polling()

        print(f"[*] Waiting max. {timeout/60} min for button click in Telegram...")
        
        try:
            await asyncio.wait_for(self.event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            print("[*] Timeout reached! Auto-Approving.")
            self.decision = "approve"
            
            if self.last_message_id:
                await self._update_message_status(
                    self.bot,
                    TELEGRAM_CHAT_ID,
                    self.last_message_id,
                    "<b>⏳ STATUS: Auto-Approved (Timeout)</b>",
                    ""
                )

        # Bot sauber stoppen
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

        return self.decision == "approve"
    
    async def _handle_callback(self, update, context):
        query = update.callback_query
        await query.answer()
        
        self.decision = query.data # "approve" oder "abort"
        print(f"[*] Telegram response received: {self.decision}")

        # Status-Text basierend auf Klick festlegen
        if self.decision == "approve":
            status = "<b>✅ STATUS: Approved & Uploading...</b>"
        else:
            status = "<b>❌ STATUS: Aborted by User.</b>"

        # UI Update direkt über den Callback-Context
        await self._update_message_status(
            context.bot, 
            query.message.chat_id, 
            query.message.message_id, 
            status,
            ""
        )
        
        self.event.set()

    
    async def _update_message_status(self, bot, chat_id, message_id, status_text, original_caption):
        try:
            # 1. Buttons entfernen
            await bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=None
            )
            # 2. Status an die Caption hängen
            new_caption = f"{original_caption}\n\n{status_text}"
            await bot.edit_message_caption(
                chat_id=chat_id,
                message_id=message_id,
                caption=new_caption,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"[!] Error updating Telegram UI: {e}")
        
if __name__ == "__main__":
    mock_strat = StoryStrategy(
        voice="am_onyx",
        hook_style="Shocking",
        folder_name="AmItheAsshole",
        output_dir="data/test",
        search_query="minecraft parkour",
        reason="Dark tone fits the story",
        caption="Am I the idiot for ruining my sister's wedding? 👰🔥",
        description="I brought my kids to a child-free wedding. Now everyone is mad.",
        tags="#aita #reddit #familydrama #storytime"
    )

    async def test():
        tg = TelegramApproval()
        test_video = "data/test/test_story.mp4" # Pfad prüfen!
        
        if not os.path.exists(test_video):
            print(f"[!] Test-Video nicht gefunden unter: {test_video}")
            return

        await tg.send_video_for_approval(test_video, mock_strat)
        print("[+] Video und Strategie wurden gesendet!")
        
        await tg.wait_for_approval(timeout=5)

    asyncio.run(test())