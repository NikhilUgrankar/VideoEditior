import os
import sys
import urllib.request
import zipfile
import shutil

FFMPEG_DIR = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.join(FFMPEG_DIR, "bin")
FFMPEG_EXE = os.path.join(BIN_DIR, "ffmpeg.exe")
FFPROBE_EXE = os.path.join(BIN_DIR, "ffprobe.exe")

def ensure_ffmpeg():
    if os.path.exists(FFMPEG_EXE) and os.path.exists(FFPROBE_EXE):
        print(f"[FFmpeg] Executable found at {FFMPEG_EXE}")
        return FFMPEG_EXE, FFPROBE_EXE
    
    os.makedirs(BIN_DIR, exist_ok=True)
    
    # Check if system ffmpeg exists
    system_ffmpeg = shutil.which("ffmpeg")
    system_ffprobe = shutil.which("ffprobe")
    if system_ffmpeg and system_ffprobe:
        print(f"[FFmpeg] Found system ffmpeg at {system_ffmpeg}")
        return system_ffmpeg, system_ffprobe

    print("[FFmpeg] FFmpeg not found in PATH or bin/. Downloading static build for Windows...")
    
    # Official gyan.dev essential build download link
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    zip_path = os.path.join(BIN_DIR, "ffmpeg-release-essentials.zip")
    
    try:
        def download_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(100.0, downloaded / total_size * 100)
                sys.stdout.write(f"\rDownloading FFmpeg... {percent:.1f}% ({downloaded/(1024*1024):.1f} MB)")
                sys.stdout.flush()

        urllib.request.urlretrieve(url, zip_path, download_progress)
        print("\n[FFmpeg] Download complete. Extracting executables...")
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file in zip_ref.namelist():
                if file.endswith("ffmpeg.exe"):
                    with zip_ref.open(file) as f_in, open(FFMPEG_EXE, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                elif file.endswith("ffprobe.exe"):
                    with zip_ref.open(file) as f_in, open(FFPROBE_EXE, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                        
        if os.path.exists(zip_path):
            os.remove(zip_path)
            
        print(f"[FFmpeg] Successfully extracted FFmpeg to {BIN_DIR}")
        return FFMPEG_EXE, FFPROBE_EXE
    except Exception as e:
        print(f"[FFmpeg Error] Failed to download FFmpeg: {e}")
        return "ffmpeg", "ffprobe"

if __name__ == "__main__":
    ensure_ffmpeg()
