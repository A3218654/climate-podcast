"""逐字稿 → MP3（男聲雙主持人）。用法: python3 make_audio.py 模型資料夾 逐字稿.md 輸出.mp3
模型: kokoro-multi-lang-v1_1。只朗讀「主持人A：」「主持人B：」開頭的行。
備案用（電腦無法轉檔時）。主持人A 七七乳加巧克力 = 聲音 88（男聲）；主持人B 非雷泡泡糖 = 聲音 57（較低沉的女聲）。"""
import sys, re, subprocess, tempfile, os
import numpy as np, soundfile as sf, sherpa_onnx
from opencc import OpenCC

VOICE = {"A": 88, "B": 57}
FIX = {"調適": "條適", "調節": "條節", "調和": "條和"}  # 破音字改用同音字送去合成
SPEED = 1.3  # 約每分鐘 280 字，接近一般談話節目語速
cc = OpenCC("t2s")  # 語音模型的字典是簡體字，只在朗讀時轉換
d, md, out = sys.argv[1].rstrip("/") + "/", sys.argv[2], sys.argv[3]
tts = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(
    model=sherpa_onnx.OfflineTtsModelConfig(
        kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
            model=d + "model.onnx", voices=d + "voices.bin", tokens=d + "tokens.txt",
            data_dir=d + "espeak-ng-data", dict_dir=d + "dict",
            lexicon=d + "lexicon-us-en.txt," + d + "lexicon-zh.txt"),
        num_threads=os.cpu_count() or 4),
    rule_fsts=f"{d}date-zh.fst,{d}phone-zh.fst,{d}number-zh.fst"))

lines = []
for ln in open(md, encoding="utf-8"):
    m = re.match(r"^主持人([AB])[：:](.+)", ln.strip())
    if m:
        lines.append((m.group(1), m.group(2).strip()))
if not lines:
    sys.exit("找不到主持人台詞")

tmp = tempfile.mkdtemp()
parts = []
for i, (who, text) in enumerate(lines):
    for k, v in FIX.items():
        text = text.replace(k, v)
    a = tts.generate(cc.convert(text), sid=VOICE[who], speed=SPEED)
    sr = a.sample_rate
    seg = os.path.join(tmp, f"{i:03d}.wav")
    sf.write(seg, np.concatenate([np.array(a.samples), np.zeros(int(sr * (0.08 if len(text) <= 8 else 0.18)))]), sr)
    parts.append(seg)
    print(f"{i+1}/{len(lines)}", flush=True)

lst = os.path.join(tmp, "list.txt")
open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                "-af", "loudnorm=I=-16:TP=-1.5", "-ac", "1", "-b:a", "64k", out], check=True)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out],
                           capture_output=True, text=True).stdout)
print(f"OK {out} {dur:.0f}s")
