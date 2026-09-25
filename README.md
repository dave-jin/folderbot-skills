# folderbot-skills

[Folder Bot](https://github.com/dave-jin/folderbot) 과 함께 쓰는 볼트 정리 도구 모음입니다. Claude Code 플러그인 하나(`folderbot`)로 묶었습니다.

폴더봇은 폴더마다 AI 봇을 심어 일하는 앱입니다. 이 플러그인은 그 폴더들을 가꾸는 반복 작업을 맡습니다. 인박스에 쌓인 파일을 제자리로 보내고, 끝난 프로젝트를 보관하고, 오랜만에 여는 프로젝트를 다시 손에 잡게 합니다. Folder Bot 없이 Claude Code 만 써도 동작합니다.

## 들어 있는 것

**스킬**
- `jev-judge` — 「이 파일은 어느 폴더로 가야 하나」 같은 선택형 판단을 [Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev)(TypeSafe AI 의 분류 모델)에 먼저 맡깁니다. 중복은 로컬 해시로 거르고, 이름이 분명한 것은 Jev 가 고르고, 애매한 것만 LLM 이 직접 엽니다. 비용이 붙으면 스스로 멈춥니다.
- `start` — 오랜만에 여는 프로젝트의 현황을 모으고 지금 할 일 하나를 브리핑합니다.
- `project-charter` — 프로젝트 폴더의 목적·역할·위임 범위를 질문으로 확정해 `CLAUDE.md` 에 적습니다.

**명령**
- `/para-sort` — 인박스 항목을 PARA 원칙대로 분류하고 이동을 제안합니다(1차 분류는 `jev-judge`).
- `/archive-done` — 끝난 프로젝트를 찾아 Archive 이동을 제안합니다.
- `/project-new` — 이름 규칙에 맞는 새 프로젝트 폴더를 만듭니다.
- `/weekly-review` — 진행·정체·아카이브 후보를 한눈에 봅니다.
- `/team-vault` — 아래 볼트 팀 네 명을 소집합니다.

**에이전트 (볼트 팀)** — 역할보다 **파일 단독 소유**가 핵심입니다. 같은 파일을 둘이 쓰지 않습니다.
- `vault-updater` — 바깥 소식을 모아 각 폴더 `readme.md` 를 사실대로 갱신
- `vault-janitor` — 중복·이름·구조 정리(계획서 → 승인 → 실행)
- `vault-scout` — 마감·정체·보관 후보와 목적 정렬 점검
- `vault-secretary` — 모든 `todo.md` 담당

**템플릿** — `templates/orchestrator.md` 는 Folder Bot 의 관제 봇(오케스트레이터)이 읽는 지침입니다. 볼트의 `.claude/orchestrator.md` 로 복사해 씁니다.

## 설치

```bash
claude plugin marketplace add dave-jin/folderbot-skills
claude plugin install folderbot@folderbot-skills
```

볼트 루트의 `CLAUDE.md` 에 폴더 규칙 블록을 두면 명령과 에이전트가 그 규칙을 따릅니다. 없으면 PARA(`1. Inbox` · `2. Projects` · `3. Area` · `4. Resources` · `5. Archive`)로 봅니다.

## jev-judge 설정 (선택 · macOS)

`jev-judge` 만 따로 설정이 필요합니다. 설정하지 않으면 분류는 LLM 이 그대로 합니다.

1. **Vercel AI Gateway 키.** Vercel 팀의 AI Gateway 탭에서 결제 수단을 등록합니다. 무료 크레딧도 카드가 등록돼 있어야 열립니다. 등록만으로 돈이 나가지는 않습니다. **크레딧은 사지 마세요.** 사는 순간 유료 등급으로 넘어가 무료 크레딧이 끊깁니다. 키는 월 한도를 걸어 만듭니다.
   ```bash
   vercel ai-gateway api-keys create --name jev-judge --budget 1 --refresh-period monthly
   ```
2. **키를 키체인에 넣습니다.** 명령을 실행하면 키를 묻습니다. 셸 기록에 키가 남지 않습니다.
   ```bash
   security add-generic-password -a jev-judge -s ai-gateway -w
   ```
3. **한 번만 설정합니다.** `jev` 명령과 매일 09:10 비용 점검이 설치됩니다.
   ```bash
   zsh ~/.claude/plugins/cache/folderbot-skills/folderbot/*/skills/jev-judge/scripts/setup.sh
   export FOLDERBOT_VAULT="<볼트 루트>"
   ```
   플러그인 설치 경로가 다르면 `claude plugin details folderbot` 으로 확인합니다.

2026-09-25 기준으로 Vercel AI Gateway 에서 Jev 호출의 청구액은 0 이었습니다. 이 조건은 바뀔 수 있으므로 `jev-judge` 는 호출마다·하루마다 확인하고, 돈이 붙으면 멈춥니다(`presets/inbox-filing.json` 의 `cost_guard`).

**보내는 것**: 파일 이름·확장자·크기와 볼트 폴더 목록입니다. 파일 본문은 보내지 않습니다. 이름에 민감어가 든 항목은 이름도 보내지 않습니다. 폴더 이름에 고객사 이름이 들어 있다면 그 목록이 Vercel·TypeSafe(미국)로 나간다는 점을 알고 쓰세요.

## 안전 원칙

- 파일을 옮기거나 지우는 일은 **계획을 보여 주고 승인받은 뒤**에만 합니다. 10개가 넘는 일괄 작업은 실행 직전에 한 번 더 묻습니다.
- 중복은 이름이 아니라 **sha256 해시**로 판정합니다. 지울 때는 휴지통으로 보냅니다.
- Archive 는 새로 만들지 않습니다. 끝난 것을 옮기기만 합니다.

## English (short)

A Claude Code plugin for keeping a PARA-style vault tidy, built alongside [Folder Bot](https://github.com/dave-jin/folderbot). `jev-judge` sends only filenames (never file contents) to TypeSafe's Jev via Vercel AI Gateway for fast, confidence-scored filing suggestions, falls back to the LLM on low confidence, and blocks itself if calls stop being free. Includes `/para-sort`, `/archive-done`, `/project-new`, `/weekly-review`, `/team-vault`, four file-owning vault agents, and `start` / `project-charter` skills. Content is in Korean.

## License

MIT
