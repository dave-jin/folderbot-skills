#!/bin/zsh
# jev-judge 한 번만 하는 설정 (macOS).
#  ① 이 스킬을 ~/.local/share/jev-judge 로 복사하고 `jev` 명령을 ~/.local/bin 에 건다
#     (플러그인 설치 폴더는 버전마다 바뀌므로 고정 자리에 둔다. 플러그인을 업데이트하면 다시 돌린다)
#  ② 매일 09:10 무료 조건 점검(launchd)을 건다
#  ③ 키체인에 키가 있는지 알려 준다 — 키 발급·저장은 사용자가 한다(README 참고)
set -e
SRC="${0:A:h:h}"
DST="$HOME/.local/share/jev-judge"
mkdir -p "$DST" "$HOME/.local/bin" "$HOME/.local/state/jev-judge"
/usr/bin/rsync -a --delete "$SRC/" "$DST/"
chmod +x "$DST/scripts/jev" "$DST/scripts/jev-daily"
ln -sf "$DST/scripts/jev" "$HOME/.local/bin/jev"

PL="$HOME/Library/LaunchAgents/com.folderbot.jev-judge.daily.plist"
cat > "$PL" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.folderbot.jev-judge.daily</string>
  <key>ProgramArguments</key><array><string>/bin/zsh</string><string>$DST/scripts/jev-daily</string></array>
  <key>StartCalendarInterval</key><dict><key>Hour</key><integer>9</integer><key>Minute</key><integer>10</integer></dict>
  <key>StandardErrorPath</key><string>$HOME/.local/state/jev-judge/daily.err</string>
</dict></plist>
PLIST
launchctl bootout "gui/$(id -u)" "$PL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PL"
echo "설치: $DST · 명령 jev → ~/.local/bin/jev · 매일 09:10 점검"
if ! /usr/bin/security find-generic-password -s ai-gateway -a jev-judge >/dev/null 2>&1; then
  echo "⚠️ 키체인에 ai-gateway/jev-judge 키가 없다. 키가 없으면 jev 는 LLM 판단으로 넘어간다(README 「키 넣기」)."
fi
echo "볼트 위치: export FOLDERBOT_VAULT=\"<볼트 루트>\" 를 셸 설정에 넣는다(없으면 현재 폴더)."
