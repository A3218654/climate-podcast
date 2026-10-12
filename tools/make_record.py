"""逐字稿 → 節目頁面資料。用法:
python3 make_record.py 逐字稿.md 音檔 音檔id 輸出.json "重點1|重點2|重點3" [pilot]
逐字稿格式: 第一行「# 標題」；台詞行「主持人A：…」；「## 本集新聞來源」後每行「1. 標題（媒體，日期）— 網址」"""
import sys, re, json, subprocess
md, audio, aid, out, hl = sys.argv[1:6]
pilot = len(sys.argv) > 6 and sys.argv[6] == "pilot"
text = open(md, encoding="utf-8").read()
m = re.search(r"climate-podcast-(\d{4})(\d{2})(\d{2})", md)
date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
title_line = re.search(r"^#\s+(.+)$", text, re.M).group(1).strip().split("｜")[-1].strip()
transcript = [{"host": a, "text": t.strip()} for a, t in re.findall(r"^主持人([AB])[：:](.+)$", text, re.M)]
sources = []
if "## 本集新聞來源" in text:
    for ln in text.split("## 本集新聞來源", 1)[1].splitlines():
        s = re.match(r"^\s*\d+\.\s*(.+?)\s*[—-]\s*(https?://\S+)\s*$", ln)
        if not s:
            continue
        head, url = s.group(1), s.group(2)
        meta = re.search(r"（([^（）]*)）\s*$", head)
        outlet = date_s = ""
        if meta:
            parts = [p.strip() for p in meta.group(1).split("，")]
            outlet = parts[0]
            date_s = parts[1] if len(parts) > 1 else ""
            head = head[: meta.start()].strip()
        sources.append({"title": head, "outlet": outlet, "date": date_s, "url": url})
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", audio],
                           capture_output=True, text=True).stdout)
rec = {"date": date, "title": title_line, "pilot": pilot, "highlights": [h.strip() for h in hl.split("|") if h.strip()],
       "transcript": transcript, "sources": sources, "audioId": aid, "duration": round(dur)}
json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"OK {date} lines={len(transcript)} sources={len(sources)} dur={round(dur)}s")
