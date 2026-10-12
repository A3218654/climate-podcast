"""把一集節目加到網站。用法（在 repo 根目錄執行）：
python3 tools/add_episode.py 節目資料.json 音檔(.mp3 或 .mp4)

節目資料.json 由 make_record.py 產生（含 date、title、highlights、transcript、sources、duration）。
音檔會存成 audio/climate-podcast-YYYYMMDD.mp3，episodes.json 裡同一天的集數會被取代。"""
import json, os, shutil, subprocess, sys

rec_path, audio_src = sys.argv[1], sys.argv[2]
rec = json.load(open(rec_path, encoding="utf-8"))
day = rec["date"].replace("-", "")
rec.pop("audioId", None)
rec["id"] = day
dest = f"audio/climate-podcast-{day}.mp3"
os.makedirs("audio", exist_ok=True)
if audio_src.lower().endswith(".mp3"):
    if os.path.abspath(audio_src) != os.path.abspath(dest):
        shutil.copyfile(audio_src, dest)
else:
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", audio_src, "-vn", "-ac", "1", "-b:a", "48k", dest], check=True)
rec["audio"] = dest
dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", dest],
                     capture_output=True, text=True).stdout.strip()
if dur:
    rec["duration"] = round(float(dur))

data = json.load(open("episodes.json", encoding="utf-8"))
eps = [e for e in data.get("episodes", []) if e.get("id") != day]
eps.append(rec)
eps.sort(key=lambda e: e.get("date", ""), reverse=True)
data["episodes"] = eps
json.dump(data, open("episodes.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"OK {day} {dest} episodes={len(eps)}")
