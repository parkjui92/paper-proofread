#!/usr/bin/env python3
"""Validate located protected spans against proposed paragraph edits.

Contextual identification belongs to the proofreading workflow. This module
checks its explicit manifest; it does not infer quotations from punctuation.
All offsets are Python string indices in the original paragraph, end-exclusive.
"""
import argparse
import json
import re
import sys


KINDS = {"interview", "quotation", "survey", "official_name", "statistics",
         "user_term", "uncertain"}
# Whitespace may change; identifiers, numbers and operators must not.
STAT_TOKEN = re.compile(r"(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][+-]?\d+)?|[^\W\d_]\w*|[^\s]", re.UNICODE)


class ProtectionError(ValueError):
    pass


def _integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _paragraph_map(paragraphs):
    texts = {}
    if not isinstance(paragraphs, list):
        raise ProtectionError("paragraphs는 문단 목록이어야 한다")
    for p in paragraphs:
        if not isinstance(p, dict) or not _integer(p.get("pid")) or not isinstance(p.get("text"), str):
            raise ProtectionError("각 문단에는 정수 pid와 text 문자열이 필요하다")
        if p["pid"] in texts:
            raise ProtectionError("중복 pid: %s" % p["pid"])
        texts[p["pid"]] = p["text"]
    return texts


def _spans(texts, spec):
    spans = spec.get("protected_spans", [])
    terms = spec.get("protected_terms", [])
    if not isinstance(spans, list) or not isinstance(terms, list):
        raise ProtectionError("protected_spans와 protected_terms는 목록이어야 한다")
    checked = []
    for s in spans:
        if not isinstance(s, dict):
            raise ProtectionError("보호 구간은 객체여야 한다")
        pid, start, end = s.get("pid"), s.get("start"), s.get("end")
        if not _integer(pid) or pid not in texts:
            raise ProtectionError("보호 구간의 pid가 없다: %s" % pid)
        if not _integer(start) or not _integer(end) or not 0 <= start < end <= len(texts[pid]):
            raise ProtectionError("pid %s: 보호 구간 좌표가 잘못되었다" % pid)
        if s.get("text") != texts[pid][start:end]:
            raise ProtectionError("pid %s: 보호 구간 원문과 좌표가 일치하지 않는다" % pid)
        if not isinstance(s.get("kind"), str) or s["kind"] not in KINDS or not isinstance(s.get("reason"), str) or not s["reason"].strip():
            raise ProtectionError("pid %s: 보호 유형과 사유가 필요하다" % pid)
        checked.append(dict(s))
    for term in terms:
        if not isinstance(term, str) or not term.strip():
            raise ProtectionError("protected_terms에는 비어 있지 않은 문자열만 쓴다")
        for pid, text in texts.items():
            start = text.find(term)
            while start >= 0:
                checked.append({"pid": pid, "start": start, "end": start + len(term),
                                "text": term, "kind": "user_term", "reason": "사용자 지정 용어"})
                start = text.find(term, start + 1)
    return checked


def _plans(texts, edits):
    if not isinstance(edits, list):
        raise ProtectionError("edits는 목록이어야 한다")
    grouped = {}
    for e in edits:
        if not isinstance(e, dict) or not _integer(e.get("pid")) or e["pid"] not in texts:
            raise ProtectionError("편집 대상 pid가 없다")
        pid, old, new = e["pid"], e.get("old"), e.get("new", "")
        if not isinstance(old, str) or not old or not isinstance(new, str):
            raise ProtectionError("pid %s: old/new 문자열이 필요하다" % pid)
        text = texts[pid]
        start = text.find(old)
        if start < 0 or text.find(old, start + 1) >= 0:
            raise ProtectionError("pid %s: old는 원문에 정확히 한 번 있어야 한다" % pid)
        if old == new:
            raise ProtectionError("pid %s: old와 new가 같다" % pid)
        grouped.setdefault(pid, []).append((start, start + len(old), new))
    for pid, plans in grouped.items():
        plans.sort()
        if any(a[1] > b[0] for a, b in zip(plans, plans[1:])):
            raise ProtectionError("pid %s: 편집 구간이 겹친다" % pid)
    return grouped


def validate_protection(paragraphs, spec):
    """Raise before writing anything when an edit changes a protected span.

Edits crossing a protected boundary are deliberately rejected, even when the
replacement repeats the protected words. Split those edits outside the span.
For statistics, only edits contained inside the span may change whitespace.
"""
    if not isinstance(spec, dict):
        raise ProtectionError("교정 지시는 객체여야 한다")
    texts = _paragraph_map(paragraphs)
    spans = _spans(texts, spec)
    grouped = _plans(texts, spec.get("edits", []))
    for span in spans:
        pid, start, end = span["pid"], span["start"], span["end"]
        touching = [p for p in grouped.get(pid, []) if p[0] < end and start < p[1]]
        if not touching:
            continue
        label = "pid %s [%s:%s] %s (%s)" % (pid, start, end, span["kind"], span["reason"])
        if span["kind"] != "statistics":
            raise ProtectionError("원문 보호 구간 변경 금지: " + label)
        if any(a < start or b > end for a, b, _ in touching):
            raise ProtectionError("보호 구간 경계를 넘는 편집은 나누어 제시: " + label)
        revised = span["text"]
        for a, b, new in reversed(touching):
            revised = revised[:a-start] + new + revised[b-start:]
        if STAT_TOKEN.findall(revised) != STAT_TOKEN.findall(span["text"]):
            raise ProtectionError("통계 표기의 수치·변수·연산자 변경 금지: " + label)
    return {"ok": True, "protected_spans": len(spans), "edits": len(spec.get("edits", []))}


def main(argv=None):
    parser = argparse.ArgumentParser(description="문단 추출본과 교정 지시의 원문 보호 검사")
    parser.add_argument("paragraphs", help="source_hash와 paragraphs가 있는 JSON")
    parser.add_argument("edits", help="source_hash, protected_spans, edits가 있는 JSON")
    args = parser.parse_args(argv)
    try:
        with open(args.paragraphs, encoding="utf-8") as f:
            source = json.load(f)
        with open(args.edits, encoding="utf-8") as f:
            spec = json.load(f)
        if not isinstance(source, dict) or not isinstance(spec, dict):
            raise ProtectionError("추출본과 교정 지시는 객체여야 한다")
        if not source.get("source_hash") or source["source_hash"] != spec.get("source_hash"):
            raise ProtectionError("원본 해시가 없거나 서로 다르다")
        if "protected_spans" not in spec:
            raise ProtectionError("보호 구간 검토 후 protected_spans를 기록해야 한다(없으면 [])")
        result = validate_protection(source.get("paragraphs"), spec)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, ValueError) as exc:
        print("원문 보호 검사 실패: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
