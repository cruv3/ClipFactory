import time
import asyncio

from reddit_scraper import RedditScraper
from script_rewriter import ScriptRewriter
from story_analyzer import StoryAnalyzer
from voice_engine import VoiceEngine
from video_engine import VideoEngine
from video_engine_old import VideoEngineOld
from video_uploader import VideoUploader
from telegram_bot import TelegramApproval
from stat_reporter import StatReporter
from music_engine import MusicEngine
from utils import clean_data_folder

import config

async def main_loop():
    scraper = RedditScraper()

    if not config.USE_RTX_XX90:
        rewriter = ScriptRewriter(0.6, 0.9, 4096)
    else:
        rewriter = None
    analyzer = StoryAnalyzer()
    voice_eng = VoiceEngine()
    video_eng = VideoEngineOld()
    uploader = VideoUploader()
    tg_bot = TelegramApproval()
    reporter = StatReporter()
    music_eng = MusicEngine()

    print("\n" + "="*40)
    print("🚀 VIRAL VIDEO FACTORY STARTED")
    print(f"[*] Post Interval: {config.VIDEO_INTERVAL_HOURS}h")
    print(f"[*] Cleanup every: {config.CLEAN_INTERVAL_HOURS}h")
    print(f"[*] Report every: {config.REPORT_INTERVAL_HOURS}h")
    print("="*40 + "\n")

    last_clean_time = time.time()
    last_report_time = time.time()

    while True:
        try:
            # 1. Cleanup Check
            current_time = time.time()
            if (current_time - last_clean_time) / 3600 >= config.CLEAN_INTERVAL_HOURS:
                print(f"[*] Starting Periodic Cleanup in {config.DATA_DIR}...")
                clean_data_folder()
                last_clean_time = time.time()

            # Periodic Stat Report
            if (current_time - last_report_time) / 3600 >= config.REPORT_INTERVAL_HOURS:
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
            script = ""
            if config.USE_RTX_XX90:
                print("[*] Extracting Narration from Strategy-Timeline...")
                if getattr(strategy, 'script_timeline', None):
                    # Zieht alle 'narration' Texte raus und verbindet sie mit einem Leerzeichen
                    script = " ".join([block.get("narration", "").strip() for block in strategy.script_timeline])
                else:
                    print("[!] Error: No script_timeline found in High-End Mode!")
            else:
                print("[*] Classic Mode: Rewriting story with separate Script Writer...")
                script = rewriter.rewrite(raw_story, strategy)
            
            if not script: 
                print("[!] Script is empty. Skipping...")
                continue

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
                word_timestamps=word_timestamps,
                strategy=strategy,
                audio_path=voice_path,
                bg_music_path=bg_music_path
            ) 
            if not video_path:
                print("[!] Video creation failed.")
                continue
            
            # 7. TELEGRAM APPROVAL (The Filter)
            await tg_bot.send_video_for_approval(video_path, strategy)
            is_approved = await tg_bot.wait_for_approval(timeout=1800)

            # 8. UPLOAD
            if config.TEST_RUN:
                print(f"\n[✅] TEST RUN COMPLETE: Video created at {video_path}")
                print("[*] Skipping upload and exiting as requested.")
                return
            
            if is_approved:
                print(f"[*] Uploading to Social Media...")
                upload_results = await uploader.distribute_video(video_path, strategy)

                failed_platforms = [p for p, res in upload_results.items() if "❌ Failed" in str(res)]
                
                if failed_platforms:
                    error_msg = f"❌ <b>UPLOAD FAILED</b>\nPlatforms: {', '.join(failed_platforms)}\n\nStopping factory for investigation."
                    await tg_bot.bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=error_msg, parse_mode='HTML')
                    print(f"\n[!] CRITICAL: Upload failed on {failed_platforms}. Breaking loop.")
                    break #

                report_msg = "✅ <b>UPLOAD REPORT</b>\n━━━━━━━━━━━━━━━━━━━━\n"
                for platform, status in upload_results.items():
                    report_msg += f"<b>{platform}:</b> {status}\n"
                report_msg += "━━━━━━━━━━━━━━━━━━━━"

                await tg_bot.bot.send_message(
                    chat_id=config.TELEGRAM_CHAT_ID, 
                    text=report_msg, 
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )

                print(f"[✅] Video successfully distributed!")
                print(f"\n[*] Cycle finished. Next video in {config.VIDEO_INTERVAL_HOURS}h...")
                await asyncio.sleep(config.VIDEO_INTERVAL_HOURS * 3600)
            else:
                print(f"[🛑] Upload aborted by user via Telegram.")

        except KeyboardInterrupt:
            print("\nShutting down factory...")
            break
        except Exception as e:
            error_text = f"🚨 <b>Factory Crash!</b>\n\nError: <code>{str(e)}</code>"
            try:
                await tg_bot.bot.send_message(config.TELEGRAM_CHAT_ID, error_text, parse_mode='HTML')
            except: pass
            print(f"\n[CRITICAL ERROR]: {e}")
            break

if __name__ == "__main__":
    asyncio.run(main_loop())