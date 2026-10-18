#!/usr/bin/env python3
"""회귀 테스트: macOS 가 주는 NFD(자모 분해) 한글 이름이 never_send·mask 를 빠져나가지 않는가.

macOS 는 한글 파일 이름을 NFD 로 준다. 그래서 `'계약서' in NFD('구매계약서.pdf')` 가 False 가 되어,
민감어 파일이 걸러지지 않고 가려야 할 이름도 그대로 나갈 수 있었다.
네트워크는 쓰지 않는다 — http 를 가로채 보낼 본문만 본다.
실행: python3 tests/test_nfd.py
"""
import argparse, importlib.machinery, importlib.util, io, json, os, sys, tempfile, unicodedata
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
NFD = lambda s: unicodedata.normalize("NFD", s)
NAME = "홍길동"  # 가려야 할 이름(예시)

tmp = Path(tempfile.mkdtemp())
preset = json.loads((HERE / "presets" / "inbox-filing.json").read_text(encoding="utf-8"))
preset["mask"] = {NAME: "본인"}
(tmp / "preset.json").write_text(json.dumps(preset, ensure_ascii=False), encoding="utf-8")
os.environ["FOLDERBOT_VAULT"] = str(tmp / "vault")
os.environ["JEV_STATE_DIR"] = str(tmp / "_state")
os.environ["JEV_PRESET"] = str(tmp / "preset.json")
loader = importlib.machinery.SourceFileLoader("jev", str(HERE / "scripts" / "jev"))
spec = importlib.util.spec_from_loader("jev", loader)
jev = importlib.util.module_from_spec(spec)
loader.exec_module(jev)

sent = []
def fake_http(method, url, body=None, auth=True, timeout=30):
    if body is not None:
        sent.append(json.dumps(body, ensure_ascii=False))
    return json.dumps({"answers": {"dest": {"choice": "모름", "confidence": 0.1, "probabilities": {}}}})
jev.http = fake_http
jev.pricecheck = lambda force=False, quiet=False: {"blocked": False}
jev.record_cost = lambda c: None

fails = []
def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        fails.append(msg)

inbox = preset["folders"]["inbox"]
project_top = preset["folders"]["candidates"][0][0]

# ① 함수 단위
check(jev.sensitive(NFD("구매계약서.pdf"), preset) == "계약서", "NFD 이름이 never_send 에 걸린다")
check(jev.mask(NFD(f"탑승권_{NAME}.pdf"), preset) == "탑승권_본인.pdf", "NFD 이름이 가려진다")

# ② 인박스 전 과정 — 가짜 볼트
vault = tmp / "vault"
(vault / inbox).mkdir(parents=True)
(vault / project_top / NFD("2026-10_강의-테스트")).mkdir(parents=True)
for n in ["구매계약서.pdf", f"탑승권_{NAME}.pdf", "회의록.md"]:
    (vault / inbox / NFD(n)).write_bytes(os.urandom(64))
sub = vault / inbox / NFD("주민센터")
sub.mkdir()
(sub / "a.pdf").write_bytes(os.urandom(64))

buf = io.StringIO()
with redirect_stdout(buf):
    jev.cmd_inbox(argparse.Namespace(limit=None))
rows = [json.loads(l) for l in buf.getvalue().splitlines()]
by = {unicodedata.normalize("NFC", r["item"]).split("/")[-1]: r for r in rows}

check(by["구매계약서.pdf"]["engine"] == "llm", "NFD 민감어 파일은 보내지 않는다")
check(by["주민센터"]["engine"] == "llm", "NFD 민감어 폴더도 보내지 않는다")
check(by[f"탑승권_{NAME}.pdf"]["engine"] == "jev", "이름이 든 파일은 가린 뒤 보낸다")
allsent = "\n".join(sent)
flat = unicodedata.normalize("NFC", allsent)  # 검사도 NFD 에 눈멀지 않게
check("계약서" not in flat and "주민" not in flat, "전송 본문에 민감어가 없다")
check(NAME not in flat and "본인" in flat, "전송 본문에 가릴 이름이 없고 「본인」이 있다")
check(allsent == unicodedata.normalize("NFC", allsent), "전송 본문 전체가 NFC 다(후보 폴더 목록 포함)")
check(f"{project_top}/2026-10_강의-테스트" in allsent, "후보 폴더 키가 NFC 로 나간다")

# ③ choice — 마지막 관문
sent.clear()
r = jev.evaluate(NFD(f"{NAME} 계약서 사본"), {"a": "가"}, "고른다", preset)
check(r.get("error") == "refused" and not sent, "evaluate 마지막 관문이 NFD 민감어를 막는다")

print(f"\n{'실패 ' + str(len(fails)) + '건' if fails else '전부 통과'}")
sys.exit(1 if fails else 0)
