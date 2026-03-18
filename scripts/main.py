import time
import asyncio

from reddit_scraper import RedditScraper
from script_rewriter import ScriptRewriter
from story_analyzer import StoryAnalyzer
from voice_engine import VoiceEngine
from video_engine import VideoEngine
from video_uploader import VideoUploader
from telegram_bot import TelegramApproval
from stat_reporter import StatReporter
from music_engine import MusicEngine
from utils import clean_data_folder

from config import (
    TELEGRAM_CHAT_ID, 
    VIDEO_INTERVAL_HOURS, CLEAN_INTERVAL_HOURS,
    DATA_DIR, TEST_RUN, REPORT_INTERVAL_HOURS
)

async def main_loop():
    scraper = RedditScraper()
    rewriter = ScriptRewriter(0.6, 0.9, 4096)
    analyzer = StoryAnalyzer(0.7, 0.9)
    voice_eng = VoiceEngine()
    video_eng = VideoEngine()
    uploader = VideoUploader()
    tg_bot = TelegramApproval()
    reporter = StatReporter()
    music_eng = MusicEngine()

    print("\n" + "="*40)
    print("🚀 VIRAL VIDEO FACTORY STARTED")
    print(f"[*] Post Interval: {VIDEO_INTERVAL_HOURS}h")
    print(f"[*] Cleanup every: {CLEAN_INTERVAL_HOURS}h")
    print(f"[*] Report every: {REPORT_INTERVAL_HOURS}h")
    print("="*40 + "\n")

    last_clean_time = time.time()
    last_report_time = time.time()

    while True:
        if not rewriter.model_verified or not analyzer.model_verified or not voice_eng.model_verified:
            if not voice_eng.model_verified:
                voice_eng.model_verified = voice_eng.verify_kokoro()  
            print("[*] Waiting for backends (Ollama/Kokoro) to be ready...")
            await asyncio.sleep(30)
            continue

        try:
            # 1. Cleanup Check
            current_time = time.time()
            if (current_time - last_clean_time) / 3600 >= CLEAN_INTERVAL_HOURS:
                print(f"[*] Starting Periodic Cleanup in {DATA_DIR}...")
                clean_data_folder()
                last_clean_time = time.time()

            # Periodic Stat Report
            if (current_time - last_report_time) / 3600 >= REPORT_INTERVAL_HOURS:
                print("[*] Analyzing periodic stat report...")
                await reporter.let_ai_analyze()
                last_report_time = time.time()

            # 2. Scraping
            raw_story = scraper.get_top_story()
            if not raw_story:
                print("[!] No new stories found. Sleeping 30m...")
                await asyncio.sleep(1800)
                continue
            
            # 3. AI Analysis (Voice, Strategy, Captions)
            strategy = analyzer.analyzer(raw_story)
            if not strategy:
                print("[!] Analysis failed. Retrying cycle...")
                continue
            
            # 4. Rewriting
            script = rewriter.rewrite(raw_story, strategy)
            if not script: continue

            # 5. Voice Generation
            voice_path = voice_eng.generate_audio(
                text=script, 
                strategy=strategy,
            )

            if not voice_path: continue
            word_timestamps = voice_eng.get_word_timestamps(voice_path)

            # 6. Video Assembly
            bg_music_path = music_eng.fetch_background_music(strategy)
            video_path = video_eng.create_video(
                original_script=script,
                word_timestamps=word_timestamps,
                strategy=strategy,
                voice_path=voice_path,
                bg_music_path=bg_music_path
            ) 
            if not video_path:
                print("[!] Video creation failed.")
                continue
            
            # 7. TELEGRAM APPROVAL (The Filter)
            await tg_bot.send_video_for_approval(video_path, strategy)
            is_approved = await tg_bot.wait_for_approval(timeout=1800)

            # 8. UPLOAD
            if TEST_RUN:
                print(f"\n[✅] TEST RUN COMPLETE: Video created at {video_path}")
                print("[*] Skipping upload and exiting as requested.")
                return
            
            if is_approved:
                print(f"[*] Uploading to Social Media...")
                upload_results = await uploader.distribute_video(video_path, strategy)

                failed_platforms = [p for p, res in upload_results.items() if "❌ Failed" in str(res)]
                
                if failed_platforms:
                    error_msg = f"❌ <b>UPLOAD FAILED</b>\nPlatforms: {', '.join(failed_platforms)}\n\nStopping factory for investigation."
                    await tg_bot.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=error_msg, parse_mode='HTML')
                    print(f"\n[!] CRITICAL: Upload failed on {failed_platforms}. Breaking loop.")
                    break #
                
                report_msg = "✅ <b>UPLOAD REPORT</b>\n━━━━━━━━━━━━━━━━━━━━\n"
                for platform, status in upload_results.items():
                    report_msg += f"<b>{platform}:</b> {status}\n"
                report_msg += "━━━━━━━━━━━━━━━━━━━━"

                await tg_bot.bot.send_message(
                    chat_id=TELEGRAM_CHAT_ID, 
                    text=report_msg, 
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )

                print(f"[✅] Video successfully distributed!")
                print(f"\n[*] Cycle finished. Next video in {VIDEO_INTERVAL_HOURS}h...")
                await asyncio.sleep(VIDEO_INTERVAL_HOURS * 3600)
            else:
                print(f"[🛑] Upload aborted by user via Telegram.")

        except KeyboardInterrupt:
            print("\nShutting down factory...")
            break
        except Exception as e:
            error_text = f"🚨 <b>Factory Crash!</b>\n\nError: <code>{str(e)}</code>"
            try:
                await tg_bot.bot.send_message(TELEGRAM_CHAT_ID, error_text, parse_mode='HTML')
            except: pass
            print(f"\n[CRITICAL ERROR]: {e}")
            break

if __name__ == "__main__":
    asyncio.run(main_loop())