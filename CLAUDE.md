# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A static, single-page tool (`index.html`) that turns Markdown or Flex JSON into a LINE Flex Message and shares it from a personal LINE account via LIFF `liff.shareTargetPicker()`. No official account, no push API, no build step, no tests. It is hosted on GitHub Pages and loaded as the endpoint of a LIFF app.

This repo is a fork (`wofylo/liff-flex-share`, upstream `ianTPE/liff-flex-share`, no license file). The LIFF ID in `index.html` belongs to the `meeting-card` LINE Login channel, not upstream's. `guide.html`, `demo.html`, `jev-proof.html` and `assets/` are upstream tutorial/demo content unrelated to the weekly workflow.

## Deploy and run

- Deploy = push to `main`. Pages (branch `main`, root) serves `https://wofylo.github.io/liff-flex-share/`. A build takes 1–2 minutes; check `gh api repos/wofylo/liff-flex-share/pages/builds/latest --jq .status`.
- The tool only works through the LIFF URL `https://liff.line.me/2012578447-PvSZyzEe` (it redirects to LINE login). Opening the Pages URL directly will not give a LIFF session.
- Syntax-check the page script: extract the last `<script>` block and run `node --check` on it.
- Weekly workflow (run from `weekly/`): `python weekly_card.py --dry-run` prints the card and logs the share-URL length without opening anything. `python weekly_card.py` opens Chrome, shows a toast, and sends nothing. `./register_task.ps1 [-Time HH:MM]` (re)registers the Windows Task Scheduler job `WeeklyMeetingCard` (Thursday, default 18:50, wake-to-run, runs only while logged in).
- Dependencies: Python 3 with PyYAML. `tzdata` is optional (falls back to fixed UTC+8 for `Asia/Taipei`).

## Architecture

Two parts that meet through a URL.

1. **`index.html`**: Markdown is parsed with `marked`, converted to Flex bubbles (`toFlex`, splits into a carousel at about 24 KB per bubble, max 12), or raw JSON starting with `{` is sent as-is (`jsonFlex`). `main()` does `liff.init`, forces `liff.login()` outside LINE, then picks the card: `?d=` (base64url UTF-8 Flex message JSON) first, then `?f=name` (loads `flex/name.json`), otherwise the textarea. `paramFromUrl` looks in `location.search`, then `liff.state`, then `liffRedirectUri`, because LINE login moves the original query there. `d` is also stashed in `sessionStorage` before the login redirect and cleared once loaded. Sharing is always a human click on `#share`.
2. **`weekly/weekly_card.py`**: reads local `weekly/config.yaml`, computes the next meeting date (`weekday` in config, Monday=0), builds the Flex message in `build_card`, encodes it into `https://liff.line.me/<liff_id>?d=<token>`, saves the URL to `weekly/last_share_url.txt`, copies it to the clipboard, opens the browser and raises a toast. The card layout lives in `build_card`, not in `index.html`.

## Constraints that are not obvious

- **Keep secrets out of the repo.** The repo and Pages site are public. The Zoom link, password and sheet link exist only in `weekly/config.yaml`, and the card only travels in the `?d=` URL. Never put them in `flex/*.json` or `config.example.yaml`. `config.yaml`, `weekly_card.log` and `last_share_url.txt` are git-ignored; `last_share_url.txt` contains the password in decodable form.
- Do not rely on a private repo: Pages from a private repo needs a paid plan, and the LIFF endpoint must be publicly reachable anyway.
- The share URL is about 2 KB. `MAX_URL` in `weekly_card.py` aborts above 7000 characters. If a card grows, switch to passing short fields rather than the whole JSON.
- When running Python against downloaded or untrusted files use `-I`. Note that `-I` hides the user-site `tzdata`, which is why the fallback exists.
- LIFF setup lives outside the repo: LINE Login channel `meeting-card` (provider WAIBot), LIFF size Full, scope `profile`, endpoint URL equal to the Pages URL, Share target picker must be on. A Messaging API channel cannot host LIFF.
- Git: use the `wofylo` account, not the active `rpwofy` one. Over HTTPS: `GH_TOKEN=$(gh auth token -u wofylo)` and `git -c credential.helper= -c "credential.helper=!gh auth git-credential" push`. The SSH key on this machine belongs to `rpwofy`. The local repo identity is `wofylo` with a noreply email.
