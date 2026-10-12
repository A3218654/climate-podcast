"""把電腦產生的逐句語音（.zip）接成一集對話音檔。
用法：python3 tools/stitch.py climate-podcast-YYYYMMDD.zip 輸出.mp3

每句先剪掉頭尾的靜音，再依對話節奏加上短停頓：
- 換人講話：約 0.2 秒
- 下一句是很短的回應（例如「對啊」「哇」）：0.08 秒，像接話
- 同一個人連續兩句：0.3 秒"""
import json, os, subprocess, sys, tempfile, zipfile

src, out = sys.argv[1], sys.argv[2]
SR = 24000
tmp = tempfile.mkdtemp()
with zipfile.ZipFile(src) as z:
    z.extractall(tmp)
manifest = json.load(open(os.path.join(tmp, "manifest.json"), encoding="utf-8"))

TRIM = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.04,"
        "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.06,areverse")


def ff(*args):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *args], check=True)


def silence(sec, path):
    ff("-f", "lavfi", "-i", f"anullsrc=r={SR}:cl=mono", "-t", f"{sec:.3f}", "-c:a", "pcm_s16le", path)


parts = []
for k, m in enumerate(manifest):
    wav = os.path.join(tmp, f"{m['i']:03d}.wav")
    ff("-i", os.path.join(tmp, m["file"]), "-af", TRIM, "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", wav)
    parts.append(wav)
    if k + 1 < len(manifest):
        nxt = manifest[k + 1]
        if nxt["chars"] <= 8:
            gap = 0.08
        elif nxt["host"] == m["host"]:
            gap = 0.30
        else:
            gap = 0.20
        g = os.path.join(tmp, f"{m['i']:03d}_gap.wav")
        silence(gap, g)
        parts.append(g)

lst = os.path.join(tmp, "list.txt")
with open(lst, "w") as f:
    f.writelines(f"file '{p}'\n" for p in parts)
ff("-f", "concat", "-safe", "0", "-i", lst, "-af", "loudnorm=I=-16:TP=-1.5", "-ac", "1", "-ar", str(SR), "-b:a", "48k", out)
dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out],
                     capture_output=True, text=True).stdout.strip()
print(f"OK {out} {float(dur):.0f}s lines={len(manifest)}")
