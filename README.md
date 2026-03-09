# ClipFactory

> A fully automated, 100% local, headless AI video generation pipeline. Optimized for low-VRAM GPUs (6GB+) to mass-produce short-form content (TikTok, Shorts, Reels) while bypassing AI-detection algorithms.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Why this exists
Most automated "faceless" channels fail because they use the same cloud-based API tools (like InVideo or ElevenLabs), resulting in generic content that gets flagged as "low-effort" or shadowbanned. 

This engine runs entirely on your own hardware (tested on a GTX 1660 Ti 6GB). It uses an LLM-driven "Analyzer" to adapt the video style to the story, applies FFmpeg obfuscation to bypass duplicate-content detection, and costs **$0** to operate.

## Core Features
* **Zero API Costs:** Runs completely offline using local Docker containers.
* **Low-VRAM Optimized:** Designed to run smoothly on 6GB GPUs by sequentially loading tasks.
* **Smart Trend Analyzer:** Uses `llama3.2` to analyze the scraped text and dynamically pick the best TTS voice, background gameplay, and hook-style.
* **AI-Detection Bypass:** Uses dynamic FFmpeg filters (color shifts, hflip, random cuts, micro-noise) to ensure every rendered video has a mathematically unique hash.
* **Built-in Analytics Loop:** Automatically logs generated content and analyzes performance via a daily reporting script.

## Architecture

1. **Scraper (`scraper.py`)** -> Pulls top text content (e.g., Reddit JSON).
2. **Analyzer (`analyzer.py`)** -> LLM decides on the "vibe" (Voice, Gameplay, Hook).
3. **Writer (`ai_writer.py`)** -> LLM rewrites the text for optimal social media retention.
4. **Voice (`voice_gen.py`)** -> Kokoro-FastAPI generates hyper-realistic TTS.
5. **Video Engine (`video_engine.py`)** -> FFmpeg slices random gameplay, syncs audio, and applies obfuscation filters.
6. **Master Loop (`main.py`)** -> The headless orchestrator running 24/7 on a timer.
