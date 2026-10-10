#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hwpx_revise — 한글 문서(.hwpx)를 제자리에서 교정하고 고친 데를 파란색으로 표시한다.

  extract  문서 → 문단 목록(JSON). 교정할 원고를 뽑는다.
  apply    문단별 교체 지시(JSON) → 교정본 2종 생성
             ① 검토본  : 넣은 글 파란색 + 뺀 글 파란 취소선  (무엇을 고쳤는지 보인다)
             ② 최종본  : 교정 반영, 표시 없음               (그대로 제출한다)
  verify   원본 ↔ 산출물 불변식 검사
  selftest 자체검사

설계 규율 (rnd-hwpx-export 「기존 hwpx 직접 편집」에서 계승):
  · <hp:t>는 서식 경계마다 잘려 있다 → 문단 단위로 이어붙여 좌표를 잡고 되돌려 쓴다
  · 표 셀은 그 자체가 hp:p다 → 중첩 hp:tbl 안의 t는 그 문단 소유가 아니다(셀 경계 오탐 차단)
  · 텍스트 길이가 바뀌면 조판 캐시(linesegarray)를 지운다 → 안 지우면 한글이 옛 배치를 보여준다
  · 3대 안전장치: ①구문자열 1회 정확 매칭 아니면 한 글자도 안 고치고 중단
                  ②편집 후 불변식(표·문단 수, charPr 참조, zip) 검사
                  ③원본 해시 대조로 동시 편집 감지

문서를 재생성하지 않는다. 원본 zip 엔트리·서식·이미지·표를 그대로 두고 본문 텍스트만 손댄다.
표준 라이브러리만 사용한다.
"""
import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zipfile

VERSION = "1.0.0"

NS = {
    "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
    "hh": "http://www.hancom.co.kr/hwpml/2011/head",
    "hs": "http://www.hancom.co.kr/hwpml/2011/section",
    "hc": "http://www.hancom.co.kr/hwpml/2011/core",
}
HP = "{%s}" % NS["hp"]
HH = "{%s}" % NS["hh"]

MARK_INS = "ins"      # 넣은 글
MARK_DEL = "del"      # 뺀 글
BLUE = "#0000FF"      # 넣은 글 — 사용자 요구: 수정사항은 파란색
GRAY = "#808080"      # 뺀 글 — 파랑 하나로 두면 넣은 글과 구분이 안 된다(렌더 실측)

# 뺀 글 표시 방식.
#   실측(2026-08-22): 같은 charPr 주입 경로에서 밑줄은 렌더되는데 취소선은 두 형태 모두
#   렌더되지 않았다 — kordoc reflow 렌더러의 취소선 미구현이다(한글 본체 동작은 미확인).
#   취소선 하나에 가시성을 걸면 뷰어에 따라 '뺀 글'과 '넣은 글'이 구분되지 않으므로,
#   기본값은 취소선 + 괄호를 함께 두어 어느 뷰어에서도 구분되게 한다.
DEL_OPEN, DEL_CLOSE = "⟦", "⟧"


def _err(msg):
    sys.stderr.write("hwpx_revise: %s\n" % msg)


class Abort(Exception):
    pass


# ───────────────────────────────────────────────────────── 패키지 입출력
class Pkg(object):
    """zip 엔트리 순서·압축 방식을 보존하며 메모리에 적재."""

    def __init__(self, path):
        self.path = path
        self.names, self.data, self.info = [], {}, {}
        with zipfile.ZipFile(path) as z:
            for n in z.namelist():
                self.names.append(n)
                self.data[n] = z.read(n)
                self.info[n] = z.getinfo(n)

    def save(self, out):
        with zipfile.ZipFile(out, "w") as z:
            for n in self.names:
                # mimetype은 hwpx 규격상 무압축 선두 엔트리
                comp = zipfile.ZIP_STORED if n == "mimetype" else zipfile.ZIP_DEFLATED
                zi = zipfile.ZipInfo(n, date_time=self.info[n].date_time)
                zi.compress_type = comp
                zi.external_attr = self.info[n].external_attr
                z.writestr(zi, self.data[n])

    def sections(self):
        return [n for n in self.names
                if re.match(r"Contents/section\d+\.xml$", n)]

    def text_hash(self):
        h = hashlib.sha256()
        for n in self.sections():
            h.update(self.data[n])
        return h.hexdigest()[:16]


def register_ns(xml_text):
    for p, u in re.findall(r'xmlns:([A-Za-z0-9_.\-]+)="([^"]+)"', xml_text[:4000]):
        ET.register_namespace(p, u)


def serialize(root, original_text):
    """원본 XML 선언을 보존하며 직렬화."""
    decl = ""
    m = re.match(r"\s*<\?xml[^>]*\?>", original_text)
    if m:
        decl = m.group(0).strip()
    body = ET.tostring(root, encoding="unicode")
    return (decl + "\n" + body) if decl else body


# ───────────────────────────────────────────────────────── 문단 수집
def own_text_nodes(p, parents):
    """이 문단이 '직접 소유한' hp:t 노드만 문서 순서로 반환.

    중첩 hp:tbl(표) 안의 t는 그 셀 문단의 것이지 이 문단의 것이 아니다.
    이 격리를 빼면 표를 담은 문단에서 셀 텍스트가 이어붙어 셀 경계를 넘는 오탐이 생긴다.
    """
    out = []

    def walk(el):
        for ch in list(el):
            if ch.tag == HP + "tbl":
                continue                      # 표는 별도 문단(셀)으로 처리
            if ch.tag == HP + "t":
                out.append(ch)
            else:
                walk(ch)
    walk(p)
    return out


def collect_paragraphs(pkg):
    """(pid, section, p요소, parents맵, t노드목록, 텍스트) 목록."""
    paras = []
    trees = {}
    pid = 0
    for sec in pkg.sections():
        xml = pkg.data[sec].decode("utf-8")
        register_ns(xml)
        root = ET.fromstring(xml)
        trees[sec] = (root, xml)
        parents = {c: p for p in root.iter() for c in p}
        for p in root.iter(HP + "p"):
            tnodes = own_text_nodes(p, parents)
            if not tnodes:
                continue
            # 표 셀 안의 문단인지
            anc, kind = parents.get(p), "body"
            while anc is not None:
                if anc.tag == HP + "tc":
                    kind = "cell"
                    break
                anc = parents.get(anc)
            text = "".join((t.text or "") for t in tnodes)
            if not text.strip():
                continue
            paras.append({"pid": pid, "sec": sec, "el": p, "parents": parents,
                          "tnodes": tnodes, "text": text, "kind": kind})
            pid += 1
    return paras, trees


# ───────────────────────────────────────────────────────── charPr 복제(파란색)
class CharPrMinter(object):
    """원본 글자속성을 복제해 색만 바꾼 속성을 만든다(글꼴·크기·굵기 보존)."""

    def __init__(self, pkg):
        self.pkg = pkg
        self.name = "Contents/header.xml"
        xml = pkg.data[self.name].decode("utf-8")
        register_ns(xml)
        self.orig_xml = xml
        self.root = ET.fromstring(xml)
        self.list_el = None
        for el in self.root.iter():
            if el.tag == HH + "charProperties":
                self.list_el = el
                break
        if self.list_el is None:
            raise Abort("header.xml에서 charProperties를 찾지 못했다")
        self.by_id = {}
        for cp in self.list_el.findall(HH + "charPr"):
            self.by_id[cp.get("id")] = cp
        self.next_id = max((int(i) for i in self.by_id if i.isdigit()), default=-1) + 1
        self.cache = {}
        self.minted = 0

    def variant(self, base_id, mark):
        """base_id의 파란색(+취소선) 변종 id를 만들거나 재사용."""
        key = (base_id, mark)
        if key in self.cache:
            return self.cache[key]
        base = self.by_id.get(base_id) or self.by_id.get("0")
        if base is None:
            raise Abort("복제할 기준 charPr(%s)이 없다" % base_id)
        new = copy.deepcopy(base)
        nid = str(self.next_id)
        self.next_id += 1
        new.set("id", nid)
        new.set("textColor", GRAY if mark == MARK_DEL else BLUE)
        # 취소선: 뺀 글 표시
        for tag in (HH + "strikeout",):
            for old in new.findall(tag):
                new.remove(old)
        if mark == MARK_DEL:
            st = ET.SubElement(new, HH + "strikeout")
            st.set("type", "SOLID")
            st.set("shape", "SOLID")
            st.set("color", GRAY)
        self.list_el.append(new)
        self.by_id[nid] = new
        self.cache[key] = nid
        self.minted += 1
        return nid

    def flush(self):
        if not self.minted:
            return
        self.list_el.set("itemCnt", str(len(self.list_el.findall(HH + "charPr"))))
        self.pkg.data[self.name] = serialize(self.root, self.orig_xml).encode("utf-8")


# ───────────────────────────────────────────────────────── 편집 적용
def find_run(node, parents):
    el = parents.get(node)
    while el is not None and el.tag != HP + "run":
        el = parents.get(el)
    return el


def apply_paragraph_edits(para, edits, minter, mode, del_mark="both"):
    """한 문단에 span 교체들을 적용.

    mode: 'review'(고친 자리 표시) | 'clean'(표시 없는 최종본)
    del_mark: both=취소선+⟦⟧ / strike=취소선만 / tag=⟦삭제⟧ 자리표시 / hide=뺀 글 안 보임
    """
    tnodes, parents = para["tnodes"], para["parents"]
    # 문단 좌표계
    spans, pos = [], 0
    for t in tnodes:
        s = t.text or ""
        spans.append({"node": t, "start": pos, "end": pos + len(s), "text": s,
                      "haschild": len(list(t)) > 0})
        pos += len(s)
    full = para["text"]

    # 각 편집의 위치 확정 (1회 정확 매칭 — 안전장치 ①은 호출부에서 이미 검사)
    plans = []
    for e in edits:
        i = full.find(e["old"])
        plans.append({"s": i, "e": i + len(e["old"]), "new": e.get("new", ""), "edit": e})
    plans.sort(key=lambda x: x["s"], reverse=True)   # 뒤에서부터 고쳐야 좌표가 안 밀린다

    for pl in plans:
        s, e, new = pl["s"], pl["e"], pl["new"]
        touched = [sp for sp in spans if sp["end"] > s and sp["start"] < e]
        if not touched:
            raise Abort("편집 좌표를 t노드에 대응시키지 못했다: %r" % pl["edit"]["old"][:30])
        if any(sp["haschild"] for sp in touched):
            raise Abort("자식 요소가 있는 t노드는 편집하지 않는다(수동 처리 필요): %r"
                        % pl["edit"]["old"][:30])

        first = touched[0]
        head = first["text"][: s - first["start"]]
        last = touched[-1]
        tail = last["text"][e - last["start"]:]
        old_text = full[s:e]

        run = find_run(first["node"], parents)
        if run is None:
            raise Abort("t노드의 부모 run을 찾지 못했다")
        parent = parents.get(run)
        if parent is None:
            raise Abort("run의 부모를 찾지 못했다")
        idx = list(parent).index(run)
        base_cp = run.get("charPrIDRef", "0")

        # 원 run은 head까지만 남긴다
        first["node"].text = head
        # 사이에 걸친 노드들은 비운다
        for sp in touched[1:]:
            sp["node"].text = ""

        # 삽입할 run들을 원 run 뒤에 순서대로 넣는다
        inserts = []

        def mkrun(text, cp_id):
            r = ET.Element(HP + "run")
            for k, v in run.attrib.items():
                r.set(k, v)
            r.set("charPrIDRef", cp_id)
            t = ET.SubElement(r, HP + "t")
            t.text = text
            return r

        if mode == "review":
            if old_text and del_mark != "hide":
                if del_mark == "tag":
                    shown = DEL_OPEN + "삭제" + DEL_CLOSE
                elif del_mark == "strike":
                    shown = old_text
                else:                                   # both
                    shown = DEL_OPEN + old_text + DEL_CLOSE
                inserts.append(mkrun(shown, minter.variant(base_cp, MARK_DEL)))
            if new:
                inserts.append(mkrun(new, minter.variant(base_cp, MARK_INS)))
        else:
            if new:
                inserts.append(mkrun(new, base_cp))
        if tail:
            inserts.append(mkrun(tail, base_cp))

        for k, r in enumerate(inserts):
            parent.insert(idx + 1 + k, r)

        # 좌표계 갱신: 이 문단은 뒤에서부터 고치므로 앞쪽 span 좌표는 그대로 유효.
        # tail은 새 run으로 옮겼으니 last 노드에서 제거한다.
        if last is not first:
            last["node"].text = ""
        else:
            pass  # head만 남기고 tail은 새 run으로 이미 옮겼다
        first["text"] = head
        first["end"] = first["start"] + len(head)
        for sp in touched[1:]:
            sp["text"] = ""
            sp["end"] = sp["start"]

    # 빈 run 정리
    for t in list(tnodes):
        if (t.text or "") == "":
            run = find_run(t, parents)
            if run is None:
                continue
            others = [c for c in run if c is not t]
            if not others:
                par = parents.get(run)
                if par is not None and len(list(par)) > 1:
                    par.remove(run)


LINESEG = re.compile(r"<hp:linesegarray\b.*?</hp:linesegarray>|<hp:linesegarray\b[^>]*/>", re.S)


def strip_lineseg(xml):
    """조판 캐시 제거 — 텍스트 길이를 바꿨으면 반드시. 안 지우면 옛 배치가 그대로 보인다."""
    return LINESEG.sub("", xml)


# ───────────────────────────────────────────────────────── 명령
def cmd_extract(args):
    pkg = Pkg(args.input)
    paras, _ = collect_paragraphs(pkg)
    out = {
        "tool": "hwpx_revise", "version": VERSION,
        "source": os.path.abspath(args.input),
        "source_hash": pkg.text_hash(),
        "paragraphs": [{"pid": p["pid"], "kind": p["kind"], "text": p["text"]} for p in paras],
    }
    txt = json.dumps(out, ensure_ascii=False, indent=1)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(txt + "\n")
        print("문단 %d개 추출 → %s (해시 %s)" % (len(paras), args.out, out["source_hash"]))
    else:
        print(txt)
    return 0


def load_edits(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    if isinstance(d, list):
        d = {"edits": d}
    if not d.get("edits"):
        raise Abort("편집 지시가 비어 있다")
    return d


def cmd_apply(args):
    pkg = Pkg(args.input)
    spec = load_edits(args.edits)

    # 안전장치 ③ — 동시 편집 감지
    want = spec.get("source_hash")
    got = pkg.text_hash()
    if want and want != got:
        raise Abort("원본이 추출 시점과 다르다(해시 %s ≠ %s). 한글에서 저장했다면 "
                    "extract부터 다시 하라." % (want, got))

    paras, _ = collect_paragraphs(pkg)
    by_pid = {p["pid"]: p for p in paras}

    # 안전장치 ① — 전량 사전 검사. 하나라도 어긋나면 한 글자도 고치지 않는다.
    problems, grouped = [], {}
    for e in spec["edits"]:
        pid = e.get("pid")
        if pid not in by_pid:
            problems.append("pid %s 없음" % pid)
            continue
        text, old = by_pid[pid]["text"], e.get("old", "")
        if not old:
            problems.append("pid %s: old가 비었다" % pid)
            continue
        n = text.count(old)
        if n != 1:
            problems.append("pid %s: 구문자열이 %d회 등장(1회여야 함) — %r" % (pid, n, old[:36]))
            continue
        if e.get("new", "") == old:
            problems.append("pid %s: old와 new가 같다" % pid)
            continue
        grouped.setdefault(pid, []).append(e)
    # 같은 문단 안 겹침 검사
    for pid, es in grouped.items():
        text = by_pid[pid]["text"]
        rng = sorted((text.find(e["old"]), text.find(e["old"]) + len(e["old"])) for e in es)
        for a, b in zip(rng, rng[1:]):
            if a[1] > b[0]:
                problems.append("pid %s: 편집 구간이 겹친다" % pid)
    if problems:
        for p in problems:
            _err("  ✗ " + p)
        raise Abort("사전 검사 %d건 실패 — 아무것도 고치지 않았다" % len(problems))

    def build(mode):
        p2 = Pkg(args.input)
        minter = CharPrMinter(p2)
        paras2, trees2 = collect_paragraphs(p2)
        by2 = {p["pid"]: p for p in paras2}
        for pid, es in grouped.items():
            apply_paragraph_edits(by2[pid], es, minter, mode, getattr(args, "del_mark", "both"))
        if mode == "review":
            minter.flush()
        for sec, (root, orig) in trees2.items():
            p2.data[sec] = strip_lineseg(serialize(root, orig)).encode("utf-8")
        return p2, minter

    # 최종본은 저장 여부와 무관하게 항상 만든다 — 사실 동결 검사의 기준이기 때문이다
    clean_pkg, clean_minter = build("clean")
    clean_text = doc_text(clean_pkg)
    review_pkg, review_minter = build("review")

    stats = {}
    for mode, dest, pk, mt in (("review", args.out, review_pkg, review_minter),
                               ("clean", args.clean, clean_pkg, clean_minter)):
        if not dest:
            continue
        if os.path.exists(dest) and not args.force:
            shutil.copy2(dest, dest + ".bak")
        pk.save(dest)
        stats[mode] = {"path": dest, "charpr_minted": mt.minted}

    # 안전장치 ② — 불변식 (동결은 최종본 텍스트로)
    rep = verify(args.input, args.out, spec, clean_text=clean_text)
    if args.clean:
        rep["clean"] = verify(args.input, args.clean, spec, clean_text=clean_text)["invariants"]

    if args.log:
        write_log(args.log, args.input, spec, grouped, by_pid, rep, stats)

    print("교정 적용 %d문단 %d건" % (len(grouped), sum(len(v) for v in grouped.values())))
    for mode, st in stats.items():
        label = "검토본(파란 표시)" if mode == "review" else "최종본(표시 없음)"
        print("  %s → %s" % (label, st["path"]))
    print_verify(rep)
    return 0 if rep["ok"] else 1


# ───────────────────────────────────────────────────────── 검증
NUM_RX = re.compile(r"\d[\d,./~∼-]*\s?(?:%p|%|억|만|천|조|원|달러|명|건|개|년|월|일|회|배|위|점|시간|분|㎡|km|kg|GB|MB)?")
QUOTE_RX = re.compile(r"「[^」\n]{1,80}」|“[^”\n]{1,80}”")
ACRO_RX = re.compile(r"\b[A-Z][A-Z0-9]{2,}\b")


def doc_text(pkg):
    paras, _ = collect_paragraphs(pkg)
    return "\n".join(p["text"] for p in paras)


def verify(src_path, out_path, spec=None, clean_text=None):
    """clean_text: 사실 동결은 반드시 '최종본' 텍스트로 검사한다.

    검토본은 뺀 글을 취소선으로 남기므로 소실이 절대 안 잡힌다 —
    검토본으로 동결 검사를 하면 게이트가 통째로 무력해진다(개발 중 실측 적발).
    """
    a, b = Pkg(src_path), Pkg(out_path)
    inv, ok = {}, True

    def chk(name, cond, detail=""):
        nonlocal ok
        inv[name] = {"ok": bool(cond), "detail": detail}
        if not cond:
            ok = False

    # zip 무결성
    try:
        with zipfile.ZipFile(out_path) as z:
            bad = z.testzip()
        chk("zip 무결성", bad is None, bad or "정상")
    except Exception as ex:
        chk("zip 무결성", False, ex.__class__.__name__)

    chk("mimetype", b.data.get("mimetype", b"") == b"application/hwp+zip",
        b.data.get("mimetype", b"").decode("utf-8", "replace"))
    chk("엔트리 수", len(a.names) == len(b.names), "%d → %d" % (len(a.names), len(b.names)))

    ta, tb = b"".join(a.data[s] for s in a.sections()).decode("utf-8"), \
             b"".join(b.data[s] for s in b.sections()).decode("utf-8")
    ca = {k: len(re.findall("<hp:%s\\b" % k, ta)) for k in ("tbl", "tc", "tr", "p")}
    cb = {k: len(re.findall("<hp:%s\\b" % k, tb)) for k in ("tbl", "tc", "tr", "p")}
    for k in ("tbl", "tr", "tc", "p"):
        chk("%s 개수" % k, ca[k] == cb[k], "%d → %d" % (ca[k], cb[k]))

    # charPr 참조 무결성
    hdr = b.data["Contents/header.xml"].decode("utf-8")
    defined = set(re.findall(r'<hh:charPr id="(\d+)"', hdr))
    used = set(re.findall(r'charPrIDRef="(\d+)"', tb))
    chk("charPr 참조", used <= defined, "미정의 %s" % sorted(used - defined)[:6])
    itemcnt = re.search(r'<hh:charProperties\s+itemCnt="(\d+)"', hdr)
    chk("charProperties itemCnt", itemcnt and int(itemcnt.group(1)) == len(defined),
        "%s vs 실제 %d" % (itemcnt.group(1) if itemcnt else "?", len(defined)))

    chk("조판 캐시 제거", "<hp:linesegarray" not in tb,
        "%d개 잔존" % len(re.findall("<hp:linesegarray", tb)))

    # 사실 동결 — 최종본 기준(검토본은 뺀 글이 남아 있어 검사가 성립하지 않는다)
    sa, sb = doc_text(a), doc_text(b)
    sfreeze = clean_text if clean_text is not None else sb
    lost = []
    for rx, kind in ((NUM_RX, "수치"), (QUOTE_RX, "인용·공식명칭"), (ACRO_RX, "약어")):
        A = set(x.strip(" .,") for x in rx.findall(sa))
        B = set(x.strip(" .,") for x in rx.findall(sfreeze))
        for it in sorted(A - B):
            if len(it) >= 2:
                lost.append("[%s] %s" % (kind, it))
    # 교정안이 미리 밝힌 '의도한 소실'(edits[].allow_loss)은 위반에서 빼고 따로 보고한다
    allowed = set()
    for e in (spec or {}).get("edits", []):
        for it in e.get("allow_loss", []) or []:
            allowed.add(it.strip(" .,"))
    intended = [x for x in lost if x.split("] ", 1)[-1] in allowed]
    lost = [x for x in lost if x.split("] ", 1)[-1] not in allowed]
    chk("사실 동결(수치·인용·약어)", not lost,
        "소실 %d건%s: %s%s" % (len(lost), "" if clean_text is not None else " ※검토본 기준",
                             ", ".join(lost[:8]),
                             (" · 의도한 소실 %d건(교정안 allow_loss): %s" % (len(intended), ", ".join(intended[:8]))) if intended else ""))

    # 편집 반영 확인
    if spec:
        missing = [e for e in spec["edits"] if e.get("new") and e["new"] not in sb]
        chk("편집 반영", not missing,
            "미반영 %d건: %s" % (len(missing), "; ".join(e["new"][:24] for e in missing[:4])))

    return {"ok": ok, "invariants": inv, "src_chars": len(sa), "out_chars": len(sb)}


def print_verify(rep):
    print("\n검증")
    for k, v in rep["invariants"].items():
        print("  %s %-22s %s" % ("✓" if v["ok"] else "✗", k, v["detail"]))
    print("  본문 %d자 → %d자" % (rep["src_chars"], rep["out_chars"]))
    print("  판정: %s" % ("통과" if rep["ok"] else "실패 — 산출물을 쓰지 말 것"))


def cmd_verify(args):
    rep = verify(args.input, args.output)
    print_verify(rep)
    return 0 if rep["ok"] else 1


def write_log(path, src, spec, grouped, by_pid, rep, stats):
    L = ["# 교정 내역", "",
         "- 원본: `%s`" % os.path.basename(src),
         "- 교정: %d문단 %d건" % (len(grouped), sum(len(v) for v in grouped.values())),
         "- 검증: %s" % ("통과" if rep["ok"] else "실패"), ""]
    L.append("| # | 문단 | 신호 | 고치기 전 | 고친 뒤 | 사유 |")
    L.append("|---|---|---|---|---|---|")
    i = 0
    for pid in sorted(grouped):
        for e in grouped[pid]:
            i += 1
            new = e.get("new", "") or "*(삭제)*"
            L.append("| %d | %d | %s | %s | %s | %s |" % (
                i, pid, e.get("signal", "—"),
                e["old"].replace("|", "\\|")[:70], new.replace("|", "\\|")[:70],
                e.get("why", "").replace("|", "\\|")))
    L += ["", "## 검증 세부", ""]
    for k, v in rep["invariants"].items():
        L.append("- %s **%s** — %s" % ("✅" if v["ok"] else "❌", k, v["detail"]))
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


# ───────────────────────────────────────────────────────── 자체검사
def cmd_selftest(args):
    import tempfile
    ok = True

    def chk(name, cond, detail=""):
        nonlocal ok
        if not cond:
            ok = False
        print("[%s] %s%s" % ("PASS" if cond else "FAIL", name, (" — " + detail) if detail else ""))

    src = args.sample
    if not src or not os.path.exists(src):
        print("시험용 hwpx가 없다 (--sample 경로 지정). 구조 검사만 건너뛴다.")
        return 1

    tmp = tempfile.mkdtemp(prefix="hwpxrev_")
    ext = os.path.join(tmp, "paras.json")
    sys.argv = ["x"]
    cmd_extract(argparse.Namespace(input=src, out=ext))
    d = json.load(open(ext, encoding="utf-8"))
    chk("문단 추출", len(d["paragraphs"]) > 0, "%d개" % len(d["paragraphs"]))
    chk("표 셀 격리", any(p["kind"] == "cell" for p in d["paragraphs"]),
        "cell %d개" % sum(1 for p in d["paragraphs"] if p["kind"] == "cell"))

    # 편집 대상: '체계적인'이 든 문단
    target = next((p for p in d["paragraphs"] if "체계적인" in p["text"]), None)
    chk("편집 대상 문단 확보", target is not None)
    if not target:
        return 1
    edits = {"source_hash": d["source_hash"], "edits": [
        {"pid": target["pid"], "old": "체계적인 개선 방안을 마련하는 것이 중요하다",
         "new": "부서별 관리 기준부터 통일해야 한다", "signal": "L-KO-CHEGYE", "why": "상투 수식어"},
    ]}
    ep = os.path.join(tmp, "edits.json")
    json.dump(edits, open(ep, "w", encoding="utf-8"), ensure_ascii=False)

    rv = os.path.join(tmp, "review.hwpx")
    cl = os.path.join(tmp, "clean.hwpx")
    lg = os.path.join(tmp, "log.md")
    rc = cmd_apply(argparse.Namespace(input=src, edits=ep, out=rv, clean=cl, log=lg, force=True))
    chk("적용·검증 통과", rc == 0)

    # 검토본에 파란 charPr이 생겼는지
    hb = Pkg(rv).data["Contents/header.xml"].decode("utf-8")
    blues = re.findall(r'<hh:charPr id="(\d+)"[^>]*textColor="%s"' % BLUE, hb)
    grays = re.findall(r'<hh:charPr id="(\d+)"[^>]*textColor="%s"' % GRAY, hb)
    chk("넣은 글: 파란 글자속성", len(blues) >= 1, "%d개" % len(blues))
    chk("뺀 글: 회색 글자속성", len(grays) >= 1, "%d개" % len(grays))
    chk("뺀 글: 취소선 정의", "strikeout" in hb)
    chk("뺀 글: 괄호 표시", "⟦" in Pkg(rv).data["Contents/section0.xml"].decode("utf-8"))

    tb = Pkg(rv).data["Contents/section0.xml"].decode("utf-8")
    chk("검토본: 뺀 글 보존", "체계적인 개선 방안을 마련하는 것이 중요하다" in tb)
    chk("검토본: 넣은 글 삽입", "부서별 관리 기준부터 통일해야 한다" in tb)
    tc = Pkg(cl).data["Contents/section0.xml"].decode("utf-8")
    chk("최종본: 뺀 글 제거", "체계적인 개선 방안을 마련하는 것이 중요하다" not in tc)
    chk("최종본: 넣은 글 반영", "부서별 관리 기준부터 통일해야 한다" in tc)
    hc = Pkg(cl).data["Contents/header.xml"].decode("utf-8")
    chk("최종본: 교정 표시 없음",
        BLUE not in hc and GRAY not in hc and "⟦" not in tc)

    # 안전장치 ①: 여러 번 등장하는 구문자열은 거부
    bad = {"source_hash": d["source_hash"], "edits": [{"pid": target["pid"], "old": "의", "new": "X"}]}
    bp = os.path.join(tmp, "bad.json")
    json.dump(bad, open(bp, "w", encoding="utf-8"), ensure_ascii=False)
    try:
        cmd_apply(argparse.Namespace(input=src, edits=bp, out=os.path.join(tmp, "x.hwpx"),
                                     clean=None, log=None, force=True))
        chk("안전장치① 다중 매칭 거부", False, "중단하지 않았다")
    except Abort:
        chk("안전장치① 다중 매칭 거부", True)

    # 안전장치 ③: 해시 불일치 거부
    bad2 = {"source_hash": "deadbeefdeadbeef", "edits": edits["edits"]}
    bp2 = os.path.join(tmp, "bad2.json")
    json.dump(bad2, open(bp2, "w", encoding="utf-8"), ensure_ascii=False)
    try:
        cmd_apply(argparse.Namespace(input=src, edits=bp2, out=os.path.join(tmp, "y.hwpx"),
                                     clean=None, log=None, force=True))
        chk("안전장치③ 해시 불일치 거부", False, "중단하지 않았다")
    except Abort:
        chk("안전장치③ 해시 불일치 거부", True)

    # 사실 동결: 수치를 지우는 편집은 검증 실패해야
    num_p = next((p for p in d["paragraphs"] if "41%" in p["text"]), None)
    if num_p:
        m = re.search(r"[^.]*41%[^.]*\.", num_p["text"])
        if m:
            bad3 = {"source_hash": d["source_hash"], "edits": [
                {"pid": num_p["pid"], "old": m.group(0), "new": "등록률이 낮은 수준이다."}]}
            bp3 = os.path.join(tmp, "bad3.json")
            json.dump(bad3, open(bp3, "w", encoding="utf-8"), ensure_ascii=False)
            rc3 = cmd_apply(argparse.Namespace(input=src, edits=bp3,
                                               out=os.path.join(tmp, "z.hwpx"),
                                               clean=None, log=None, force=True))
            chk("사실 동결 위반 적발", rc3 == 1)
            # 같은 편집이라도 지울 수치를 allow_loss로 선언하면 통과해야(의도한 소실)
            gone = [x.strip(" .,") for x in NUM_RX.findall(m.group(0)) if len(x.strip(" .,")) >= 2]
            ok3 = {"source_hash": d["source_hash"], "edits": [
                {"pid": num_p["pid"], "old": m.group(0), "new": "등록률이 낮은 수준이다.", "allow_loss": gone}]}
            bp4 = os.path.join(tmp, "ok3.json")
            json.dump(ok3, open(bp4, "w", encoding="utf-8"), ensure_ascii=False)
            rc4 = cmd_apply(argparse.Namespace(input=src, edits=bp4,
                                               out=os.path.join(tmp, "z2.hwpx"),
                                               clean=None, log=None, force=True))
            chk("의도한 소실 선언 시 통과", rc4 == 0)

    chk("변경 내역 로그 생성", os.path.exists(lg) and os.path.getsize(lg) > 100)
    print("\n자체검사: %s" % ("전건 통과" if ok else "실패 있음"))
    print("산출물: %s" % tmp)
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="hwpx 제자리 교정 — 고친 데를 파란색으로 표시")
    sp = ap.add_subparsers(dest="cmd")

    e = sp.add_parser("extract", help="문단 목록 추출(JSON)")
    e.add_argument("input"); e.add_argument("-o", "--out")
    e.set_defaults(fn=cmd_extract)

    a = sp.add_parser("apply", help="교정 적용")
    a.add_argument("input"); a.add_argument("edits")
    a.add_argument("-o", "--out", required=True, help="검토본(파란 표시)")
    a.add_argument("-c", "--clean", help="최종본(표시 없음)")
    a.add_argument("-l", "--log", help="변경 내역 md")
    a.add_argument("-f", "--force", action="store_true", help="기존 산출물 백업 없이 덮어쓰기")
    a.add_argument("--del-mark", default="both", choices=["both", "strike", "tag", "hide"],
                   dest="del_mark",
                   help="검토본에서 뺀 글 표시: both=취소선+⟦⟧(기본) / strike=취소선만 "
                        "/ tag=⟦삭제⟧ 자리표시 / hide=안 보임")
    a.set_defaults(fn=cmd_apply)

    v = sp.add_parser("verify", help="불변식 검사")
    v.add_argument("input"); v.add_argument("output")
    v.set_defaults(fn=cmd_verify)

    s = sp.add_parser("selftest", help="자체검사")
    s.add_argument("--sample", help="시험용 hwpx 경로")
    s.set_defaults(fn=cmd_selftest)

    ap.add_argument("--version", action="version", version="hwpx_revise " + VERSION)
    args = ap.parse_args(argv)
    if not getattr(args, "fn", None):
        ap.print_help()
        return 2
    try:
        return args.fn(args)
    except Abort as ex:
        _err(str(ex))
        return 2
    except (OSError, ValueError, KeyError, ET.ParseError) as ex:
        _err("%s: %s" % (ex.__class__.__name__, ex))
        return 2


if __name__ == "__main__":
    sys.exit(main())
