"""Behavioral cases for located protection, including actual HWPX output."""
import argparse
import contextlib
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from xml.sax.saxutils import escape
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import hwpx_revise as hwpx
from protected_spans import ProtectionError, validate_protection

CASES = json.loads((ROOT / "examples/protected-spans.json").read_text())["cases"]


def spec_for(case):
    spans = []
    texts = {p["pid"]: p["text"] for p in case["paragraphs"]}
    for annotation in case["protect"]:
        start = texts[annotation["pid"]].index(annotation["text"])
        spans.append(dict(annotation, start=start, end=start + len(annotation["text"])))
    return {"protected_spans": spans, "protected_terms": case["protected_terms"],
            "edits": copy.deepcopy(case["edits"])}


def write_hwpx(path, texts):
    """Minimal synthetic package; text is split across runs to exercise offsets."""
    header = '<hh:head xmlns:hh="%s"><hh:charProperties itemCnt="1"><hh:charPr id="0" textColor="#000000"><hh:fontRef hangul="0"/></hh:charPr></hh:charProperties></hh:head>' % hwpx.NS["hh"]
    paragraphs = []
    for text in texts:
        middle = len(text) // 2
        runs = ''.join('<hp:run charPrIDRef="0"><hp:t>%s</hp:t></hp:run>' % escape(part)
                       for part in [text[:middle], text[middle:]])
        paragraphs.append('<hp:p>%s<hp:linesegarray/></hp:p>' % runs)
    table = '<hp:p><hp:run charPrIDRef="0"><hp:tbl><hp:tr><hp:tc><hp:p><hp:run charPrIDRef="0"><hp:t>검증용 표</hp:t></hp:run></hp:p></hp:tc></hp:tr></hp:tbl></hp:run></hp:p>'
    section = '<hs:sec xmlns:hs="%s" xmlns:hp="%s">%s%s</hs:sec>' % (hwpx.NS["hs"], hwpx.NS["hp"], ''.join(paragraphs), table)
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('mimetype', b'application/hwp+zip')
        archive.writestr('Contents/header.xml', header)
        archive.writestr('Contents/section0.xml', section)


class ProtectionCases(unittest.TestCase):
    def test_common_guard_examples(self):
        for case in CASES:
            with self.subTest(case=case['id']):
                if case['allow']:
                    self.assertTrue(validate_protection(case['paragraphs'], spec_for(case))['ok'])
                else:
                    with self.assertRaises(ProtectionError):
                        validate_protection(case['paragraphs'], spec_for(case))

    def test_hwpx_examples_and_no_output_on_rejection(self):
        for case in CASES:
            with self.subTest(case=case['id']), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source, review, clean, log = [root / name for name in ['source.hwpx', 'review.hwpx', 'clean.hwpx', 'log.md']]
                texts = [p['text'] for p in case['paragraphs']]
                write_hwpx(source, texts)
                source_bytes = source.read_bytes()
                spec = spec_for(case)
                spec['source_hash'] = hwpx.Pkg(source).text_hash()
                # Neither legacy allow_loss nor force can override protected spans.
                for edit in spec['edits']:
                    edit['allow_loss'] = [s['text'] for s in spec['protected_spans']]
                edit_path = root / 'edits.json'
                edit_path.write_text(json.dumps(spec, ensure_ascii=False))
                args = argparse.Namespace(input=str(source), edits=str(edit_path), out=str(review),
                                          clean=str(clean), log=str(log), force=True)
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    if case['allow']:
                        self.assertEqual(hwpx.cmd_apply(args), 0)
                        actual, _ = hwpx.collect_paragraphs(hwpx.Pkg(clean))
                        expected = list(texts)
                        for edit in case['edits']:
                            expected[edit['pid']] = expected[edit['pid']].replace(edit['old'], edit['new'], 1)
                        self.assertEqual([p['text'] for p in actual], expected + ['검증용 표'])
                        self.assertTrue(review.exists() and log.exists())
                    else:
                        with self.assertRaises(hwpx.Abort):
                            hwpx.cmd_apply(args)
                        self.assertFalse(any(p.exists() for p in [review, clean, log]))
                self.assertEqual(source.read_bytes(), source_bytes)

    def test_stale_and_invalid_manifest_rejected(self):
        case = CASES[0]
        original = spec_for(case)
        for field, value in [('start', -1), ('end', 9999), ('text', '다른 원문'),
                             ('kind', 'unknown'), ('kind', []), ('reason', ''), ('pid', True)]:
            with self.subTest(field=field, value=value):
                spec = copy.deepcopy(original)
                spec['protected_spans'][0][field] = value
                with self.assertRaises(ProtectionError):
                    validate_protection(case['paragraphs'], spec)

    def test_statistics_multiple_edits_and_scope_boundary(self):
        text = '결과: M=3.21, p<.05'
        paragraphs = [{'pid': 0, 'text': text}]
        spec = {'protected_spans': [{'pid': 0, 'start': 4, 'end': len(text), 'text': text[4:],
                                    'kind': 'statistics', 'reason': '검정 결과'}],
                'edits': [{'pid': 0, 'old': 'M=', 'new': 'M = '}, {'pid': 0, 'old': 'p<', 'new': 'p < '}]}
        self.assertTrue(validate_protection(paragraphs, spec)['ok'])
        spec['edits'] = [{'pid': 0, 'old': text, 'new': text.replace('결과', '분석 결과')}]
        with self.assertRaises(ProtectionError):
            validate_protection(paragraphs, spec)

    def test_user_term_every_occurrence_and_whole_sentence_edit(self):
        paragraphs = [{'pid': 0, 'text': '기술이전'}, {'pid': 1, 'text': '기술이전도 필요하다.'}]
        spec = {'protected_spans': [], 'protected_terms': ['기술이전'],
                'edits': [{'pid': 1, 'old': '기술이전', 'new': '기술 이전'}]}
        with self.assertRaises(ProtectionError):
            validate_protection(paragraphs, spec)
        case = next(c for c in CASES if c['id'] == 'outside_quote')
        spec = spec_for(case)
        full = case['paragraphs'][0]['text']
        spec['edits'] = [{'pid': 0, 'old': full, 'new': full.replace('말하엿다', '말하였다')}]
        with self.assertRaises(ProtectionError):
            validate_protection(case['paragraphs'], spec)

    def test_guard_cli_hash_and_manifest_requirement(self):
        case = next(c for c in CASES if c['id'] == 'outside_quote')
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'paras.json'
            edit_path = Path(directory) / 'edits.json'
            source.write_text(json.dumps({'source_hash': 'fixture-sha256', 'paragraphs': case['paragraphs']}))
            for variant, expected in [('valid', 0), ('wrong_hash', 2), ('missing_spans', 2), ('changed_quote', 2)]:
                with self.subTest(variant=variant):
                    spec = spec_for(case)
                    spec['source_hash'] = 'fixture-sha256' if variant != 'wrong_hash' else 'stale'
                    if variant == 'missing_spans':
                        del spec['protected_spans']
                    if variant == 'changed_quote':
                        spec['edits'] = [{'pid': 0, 'old': '되게 ', 'new': ''}]
                    edit_path.write_text(json.dumps(spec))
                    result = subprocess.run([sys.executable, str(ROOT / 'scripts/protected_spans.py'), str(source), str(edit_path)], capture_output=True, text=True)
                    self.assertEqual(result.returncode, expected, result.stderr)

    def test_legacy_quote_check_remains(self):
        with tempfile.TemporaryDirectory() as directory:
            a, b = Path(directory) / 'a.hwpx', Path(directory) / 'b.hwpx'
            write_hwpx(a, ['“데이타”'])
            write_hwpx(b, ['“데이터”'])
            report = hwpx.verify(a, b)
            self.assertFalse(report['invariants']['사실 동결(수치·인용·약어)']['ok'])


if __name__ == '__main__':
    unittest.main()
