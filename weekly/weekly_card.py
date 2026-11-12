#!/usr/bin/env python3
"""Build this week's meeting card and open the LIFF share tool with it prefilled.

The card travels only in the URL (?d=base64url JSON); nothing is committed.
"""
import argparse
import base64
import json
import logging
import sys
import webbrowser
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml

HERE = Path(__file__).resolve().parent
LOG = logging.getLogger("weekly_card")
WEEKDAYS = "一二三四五六日"
MAX_URL = 7000


def load_config(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"config not found: {path} (copy config.example.yaml to config.yaml)")
    cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    required = ["liff_id", "timezone", "weekday", "title", "time", "meeting", "sheet_url"]
    missing = [k for k in required if k not in cfg]
    if missing:
        raise SystemExit(f"config missing keys: {', '.join(missing)}")
    for k in ("url", "password"):
        if not cfg["meeting"].get(k) or "REPLACE" in str(cfg["meeting"][k]):
            raise SystemExit(f"config meeting.{k} is not set")
    return cfg


def resolve_tz(name: str):
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        if name == "Asia/Taipei":
            LOG.warning("tzdata not installed, using fixed UTC+8 (Taipei has no DST)")
            return timezone(timedelta(hours=8))
        raise SystemExit(f"timezone {name} unavailable; run: pip install tzdata")


def next_meeting_date(cfg: dict, today=None):
    now = today or datetime.now(resolve_tz(cfg["timezone"]))
    days_ahead = (int(cfg["weekday"]) - now.weekday()) % 7
    return (now + timedelta(days=days_ahead)).date()


def row(label: str, value: str, action_uri: str | None = None) -> dict:
    value_span = {"type": "span", "text": value}
    comp = {
        "type": "text", "wrap": True, "size": "sm", "color": "#222222", "margin": "sm",
        "contents": [{"type": "span", "text": f"{label}｜", "weight": "bold"}, value_span],
    }
    if action_uri:
        comp["action"] = {"type": "uri", "uri": action_uri}
    return comp


def build_card(cfg: dict, date) -> dict:
    date_text = f"{date.month}/{date.day}（{WEEKDAYS[date.weekday()]}）"
    body = [
        {"type": "text", "text": cfg["title"], "weight": "bold", "size": "lg", "wrap": True},
        row("日期", date_text),
        row("時間", cfg["time"]),
        row("密碼", str(cfg["meeting"]["password"])),
    ]
    if cfg.get("rsvp_lines"):
        body.append({"type": "separator", "margin": "lg"})
        body += [
            {"type": "text", "text": line, "wrap": True, "size": "sm", "margin": "md", "color": "#222222"}
            for line in cfg["rsvp_lines"]
        ]
    footer = [
        {"type": "button", "style": "primary", "height": "sm",
         "action": {"type": "uri", "label": "加入會議", "uri": cfg["meeting"]["url"]}},
        {"type": "button", "style": "link", "height": "sm",
         "action": {"type": "uri", "label": "需求與表單", "uri": cfg["sheet_url"]}},
    ]
    return {
        "type": "flex",
        "altText": f"{cfg['title']} {date_text} {cfg['time']}"[:100],
        "contents": {
            "type": "bubble", "size": "mega",
            "body": {"type": "box", "layout": "vertical", "paddingAll": "16px", "contents": body},
            "footer": {"type": "box", "layout": "vertical", "spacing": "sm", "contents": footer},
        },
    }


def share_url(cfg: dict, card: dict) -> str:
    raw = json.dumps(card, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    token = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    url = f"https://liff.line.me/{cfg['liff_id']}?d={token}"
    if len(url) > MAX_URL:
        raise SystemExit(f"share URL too long ({len(url)} chars)")
    return url


def toast(title: str, message: str) -> None:
    import subprocess
    ps = (
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null;"
        "$t=[Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent('ToastText02');"
        "$n=$t.GetElementsByTagName('text');"
        f"$n.Item(0).AppendChild($t.CreateTextNode('{title}')) | Out-Null;"
        f"$n.Item(1).AppendChild($t.CreateTextNode('{message}')) | Out-Null;"
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('WeeklyCard').Show("
        "[Windows.UI.Notifications.ToastNotification]::new($t))"
    )
    result = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True)
    if result.returncode != 0:
        LOG.warning("toast failed: %s", result.stderr.strip())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", type=Path, default=HERE / "config.yaml")
    ap.add_argument("--dry-run", action="store_true", help="print card JSON and URL length, do not open browser")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(HERE / "weekly_card.log", encoding="utf-8"), logging.StreamHandler()],
    )
    cfg = load_config(args.config)
    date = next_meeting_date(cfg)
    card = build_card(cfg, date)
    url = share_url(cfg, card)
    LOG.info("meeting date %s, url length %d", date, len(url))
    if args.dry_run:
        print(json.dumps(card, ensure_ascii=False, indent=2))
        return 0
    if not webbrowser.open(url):
        LOG.error("could not open browser")
        return 1
    toast("AI 聚會卡片已備好", f"{date.month}/{date.day} 的卡片已填好，按「分享卡片」送出")
    return 0


if __name__ == "__main__":
    sys.exit(main())
