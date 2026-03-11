import asyncio
import os
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler
from telegram.request import HTTPXRequest

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
            message = await self.bot.send_video(
                chat_id=TELEGRAM_CHAT_ID,
                video=video_path,
                caption=strategy_details,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
                write_timeout=300, 
                read_timeout=300,  
                connect_timeout=300
            )
            self.last_message_id = message.message_id
            return message.message_id
        except Exception as e:
            print(f"[!] Telegram Upload Error: {e}")
    
    async def _handle_callback(self, update, context):
        query = update.callback_query
        await query.answer()
        
        self.decision = query.data
        print(f"[*] Telegram response received: {self.decision}")
        
        try:
            # Buttons entfernen
            await query.edit_message_reply_markup(reply_markup=None)

            if self.decision == "approve":
                new_status = "<b>✅ STATUS: Approved & Uploading...</b>"
            else:
                new_status = "<b>❌ STATUS: Aborted by User.</b>"
            
            updated_caption = f"{query.message.caption_html}\n\n{new_status}"
            await query.edit_message_caption(
                caption=updated_caption, 
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"[!] Error updating caption: {e}")
        
        self.event.set()

    async def wait_for_approval(self, timeout=1800):
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
                try:
                    await self.bot.edit_message_reply_markup(
                        chat_id=TELEGRAM_CHAT_ID, 
                        message_id=self.last_message_id, 
                        reply_markup=None
                    )
                    await self.bot.edit_message_caption(
                        chat_id=TELEGRAM_CHAT_ID,
                        message_id=self.last_message_id,
                        caption=f"✅ **AUTO-APPROVED (Timeout)**\n\nStarting upload now...",
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception as e:
                    print(f"[!] Could not update Telegram UI: {e}")

        # Stop bot properly
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

        return self.decision == "approve"
        
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
        tg = TelegramApproval(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
        test_video = "data/test/test_story.mp4" # Pfad prüfen!
        
        if not os.path.exists(test_video):
            print(f"[!] Test-Video nicht gefunden unter: {test_video}")
            return

        await tg.send_video_for_approval(test_video, mock_strat)
        print("[+] Video und Strategie wurden gesendet!")
        
        await tg.wait_for_approval(timeout=30)

    asyncio.run(test())