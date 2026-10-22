#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

try:
    from music21 import converter, tempo, note, meter
    HAS_MUSIC21 = True
except Exception:
    HAS_MUSIC21 = False


def parse_musicxml_basic(xml_path: Path):
    if not HAS_MUSIC21:
        raise RuntimeError("music21 未安装。请先: pip install music21")

    score = converter.parse(str(xml_path))
    # 取第一个速度标记与拍号作为全局近似
    bpm = 120
    ts = "4/4"
    for el in score.recurse():
        if isinstance(el, tempo.MetronomeMark) and el.number:
            bpm = int(el.number)
            break
    for el in score.recurse():
        if isinstance(el, meter.TimeSignature):
            ts = el.ratioString
            break

    # 简化：将所有音高符号位置映射为三车道 [0,1,2]
    notes = []
    for n in score.recurse().notes:
        if isinstance(n, note.Note):
            t_sec = float(n.offset)
            lane = n.pitch.midi % 3
            notes.append({"time": round(t_sec, 3), "lane": lane, "type": "tap"})

    notes.sort(key=lambda x: x["time"]) 
    return {
        "title": xml_path.stem,
        "bpm": bpm,
        "timesig": ts,
        "offset": 0.0,
        "audio": "res://assets/audio/example.ogg",
        "notes": notes,
    }


def main():
    parser = argparse.ArgumentParser(description="Convert MusicXML to game beatmap JSON")
    parser.add_argument("input", type=Path, help="Input MusicXML file path")
    parser.add_argument("output", type=Path, help="Output JSON file path")
    args = parser.parse_args()

    result = parse_musicxml_basic(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Wrote beatmap to {args.output}")


if __name__ == "__main__":
    main()

