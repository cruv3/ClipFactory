import os
import soundfile as sf
import numpy as np
from kokoro import KPipeline

def generate_voice(text, output_path, voice_name="af_bella", speed=1.1):
    """
    Generiert High-End Audio mit Kokoro.
    
    voice_name: z.B. 'af_bella' (American Female), 'bm_george' (British Male)
    speed: 1.0 bis 2.0 (1.1-1.2 ist ideal für TikTok/Shorts)
    """
    print(f"[*] Kokoro TTS: Generiere Audio mit Stimme '{voice_name}' (Speed: {speed})")
    
    try:
        lang_code = voice_name[0] 
    
        pipeline = KPipeline(lang_code=lang_code)

        generator = pipeline(
            text, 
            voice=voice_name, 
            speed=speed, 
            split_pattern=r'\n+'
        )

        all_audio = []
        for i, (gs, ps, audio) in enumerate(generator):
            all_audio.append(audio)
            
        if not all_audio:
            print("[!] Kokoro: Kein Audio generiert.")
            return None

        # 4. Audio-Arrays zusammenfügen
        final_audio = np.concatenate(all_audio)

        # 5. Speichern (Kokoro nutzt nativ 24.000 Hz)
        sf.write(output_path, final_audio, 24000)
        print(f"[✅] Kokoro Voice gespeichert: {output_path}")


        del pipeline
        
        return output_path

    except Exception as e:
        print(f"[!] Fehler im Kokoro-Modul: {e}")
        return None