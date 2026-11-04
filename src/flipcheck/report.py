"""Self-contained HTML report."""

from __future__ import annotations

import html
import json

from .core import QuestionResult, Summary

PALETTE = ["#2f6fdf", "#d9822b", "#2a9d8f", "#c0397a", "#7a5cc7", "#8a8f2a"]


def _pct(v):
    return "n/a" if v is None else f"{v:.0%}"


def to_html(results: list[QuestionResult], s: Summary, model_name: str = "", note: str = "") -> str:
    cards = [
        ("Flip rate", _pct(s.flip_rate), "questions whose answer changed under at least one rewording"),
        ("Mean agreement", _pct(s.mean_agreement), "share of rewordings that agree with the majority answer"),
        ("Accuracy (original wording)", _pct(s.accuracy_original), "what a normal single-prompt eval reports"),
        ("Accuracy (every wording)", _pct(s.accuracy_worst_case), "correct under all rewordings"),
        ("Stability → correctness AUROC", "n/a" if s.stability_auroc is None else f"{s.stability_auroc:.2f}",
         "does agreement work as a black-box confidence signal? 0.5 = no"),
        ("Unparsed replies", _pct(s.unparsed_rate), "replies with no extractable answer"),
    ]
    card_html = "".join(f'<div class="card"><div class="v">{v}</div><div class="k">{k}</div>'
                        f'<div class="h">{html.escape(h)}</div></div>' for k, v, h in cards)
    rows = []
    for r in sorted(results, key=lambda r: (r.agreement, r.id)):
        colors = {}
        chips = []
        for a in r.answers:
            if a in (None, ""):
                chips.append('<span class="chip none">?</span>')
                continue
            if a not in colors:
                colors[a] = PALETTE[len(colors) % len(PALETTE)]
            chips.append(f'<span class="chip" style="background:{colors[a]}" title="{html.escape(a)}"></span>')
        legend = " ".join(f'<span style="color:{c}">■</span> {html.escape(a)}' for a, c in colors.items())
        verdict = "" if r.majority_correct is None else ("✓" if r.majority_correct else "✗")
        detail = "".join(f"<li><b>{html.escape(a or '?')}</b> ← <code>{html.escape(v.splitlines()[0][:90])}</code></li>"
                         for v, a in zip(r.variants, r.answers))
        rows.append(f"""<tr class="{'flip' if r.flipped else ''}"><td>{html.escape(r.id)}</td>
<td><details><summary>{html.escape(r.question)}</summary><ul>{detail}</ul></details></td>
<td class="chips">{''.join(chips)}<div class="legend">{legend}</div></td>
<td>{r.agreement:.0%}</td><td>{html.escape(str(r.gold) if r.gold is not None else '')} {verdict}</td></tr>""")
    data = json.dumps({"summary": s.__dict__})
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>flipcheck report</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{{--bg:#fff;--fg:#1c2230;--muted:#5d6678;--line:#e4e7ec;--card:#f6f7f9}}
@media(prefers-color-scheme:dark){{:root{{--bg:#12151b;--fg:#e8ebf0;--muted:#9aa3b2;--line:#2a2f39;--card:#1a1e26}}}}
body{{font:15px/1.5 system-ui,sans-serif;background:var(--bg);color:var(--fg);max-width:1100px;margin:0 auto;padding:24px 16px}}
h1{{font-size:22px;margin:0}} .sub{{color:var(--muted);margin:4px 0 20px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-bottom:24px}}
.card{{background:var(--card);border-radius:10px;padding:14px}} .v{{font-size:26px;font-weight:650}}
.k{{font-weight:600;font-size:13px}} .h{{color:var(--muted);font-size:12px;margin-top:4px}}
table{{width:100%;border-collapse:collapse}} td,th{{border-bottom:1px solid var(--line);padding:8px;text-align:left;vertical-align:top}}
tr.flip td:first-child{{border-left:3px solid #d9822b}}
.chip{{display:inline-block;width:14px;height:14px;border-radius:3px;margin-right:3px}} .chip.none{{background:var(--line);text-align:center;font-size:10px;line-height:14px}}
.chips{{min-width:190px;white-space:nowrap}} .legend{{white-space:normal;font-size:12px;color:var(--muted);margin-top:4px}} code{{font-size:12px}} details summary{{cursor:pointer}}
.note{{color:var(--muted);font-size:13px;margin-top:20px}}
</style></head><body>
<h1>flipcheck report</h1><div class="sub">{html.escape(model_name)} · {s.n_questions} questions × {s.n_variants} rewordings</div>
<div class="cards">{card_html}</div>
<table><thead><tr><th>id</th><th>question (click for each rewording)</th><th>answer per rewording</th><th>agree</th><th>gold</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
<p class="note">{html.escape(note)}</p>
<script type="application/json" id="data">{data}</script>
</body></html>"""
