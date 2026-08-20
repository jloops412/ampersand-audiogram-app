from __future__ import annotations

# ruff: noqa: E501
import html
from collections import Counter
from pathlib import Path

from ampersand_contracts import SemanticMap, SemanticRegion

_COLORS = {
    "speech": "#16a085",
    "silence": "#607d8b",
    "music": "#8e44ad",
    "ambience": "#2980b9",
    "noise": "#d35400",
    "mixed": "#c0392b",
    "unknown": "#7f8c8d",
}


def write_semantic_debug_report(path: Path, semantic_map: SemanticMap) -> None:
    """Write a deterministic, local-only view without rendering transcript text."""

    path.parent.mkdir(parents=True, exist_ok=True)
    label_duration = Counter[str]()
    for region in semantic_map.regions:
        label_duration[region.content_label] += region.end_us - region.start_us
    kind_counts = Counter(observation.kind.value for observation in semantic_map.observations)
    provider_by_provenance = {
        provenance.provenance_id: provenance.provider_id for provenance in semantic_map.provenance_sources
    }
    provider_counts = Counter(
        provider_by_provenance.get(observation.provenance_ref, "provider:missing")
        for observation in semantic_map.observations
    )
    segments = _consolidate_regions(semantic_map.regions)

    timeline = "".join(
        (
            f'<span class="segment" title="{html.escape(label)} {start_us / 1_000_000:.1f}s-'
            f'{end_us / 1_000_000:.1f}s" style="width:{(end_us - start_us) / semantic_map.duration_us * 100:.8f}%;'
            f'background:{_COLORS[label]}"></span>'
        )
        for start_us, end_us, label in segments
    )
    label_rows = "".join(
        f"<tr><td>{html.escape(label)}</td><td>{duration / 1_000_000:.3f} s</td>"
        f"<td>{duration / semantic_map.duration_us * 100:.2f}%</td></tr>"
        for label, duration in sorted(label_duration.items())
    )
    provider_rows = "".join(
        f"<tr><td>{html.escape(provider)}</td><td>{count}</td></tr>"
        for provider, count in sorted(provider_counts.items())
    )
    kind_rows = "".join(
        f"<tr><td>{html.escape(kind)}</td><td>{count}</td></tr>" for kind, count in sorted(kind_counts.items())
    )
    region_rows = "".join(_region_row(region) for region in semantic_map.regions[:500])
    truncation = (
        f"<p>Showing the first 500 of {len(semantic_map.regions)} analysis regions.</p>"
        if len(semantic_map.regions) > 500
        else ""
    )
    warning_items = "".join(f"<li>{html.escape(warning)}</li>" for warning in semantic_map.warnings)

    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ampersand Semantic Map debug report</title>
<style>
:root {{ color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }}
body {{ margin: 0; background: #10151b; color: #eef3f7; }}
main {{ width: min(1180px, calc(100% - 32px)); margin: 32px auto 64px; }}
h1, h2 {{ letter-spacing: -.02em; }} .muted {{ color: #9fb0bf; }}
.cards {{ display: grid; grid-template-columns: repeat(auto-fit,minmax(180px,1fr)); gap: 12px; margin: 20px 0; }}
.card, section {{ background: #17212b; border: 1px solid #2a3946; border-radius: 12px; padding: 16px; }}
.value {{ font-size: 1.6rem; font-weight: 700; }}
.timeline {{ display: flex; height: 44px; overflow: hidden; border-radius: 8px; background: #27333d; margin: 18px 0; }}
.segment {{ display: block; min-width: 1px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit,minmax(260px,1fr)); gap: 12px; }}
table {{ width: 100%; border-collapse: collapse; }} th, td {{ padding: 8px; border-bottom: 1px solid #2a3946; text-align: left; }}
th {{ color: #9fb0bf; font-size: .78rem; text-transform: uppercase; }}
.scroll {{ overflow-x: auto; }} code {{ color: #8bd5ca; }}
</style>
</head>
<body><main>
<p class="muted">Ampersand-owned, provider-neutral analysis artifact</p>
<h1>Semantic Audio Map V0</h1>
<p><code>{html.escape(semantic_map.semantic_map_id)}</code></p>
<div class="cards">
  <div class="card"><div class="muted">Duration</div><div class="value">{semantic_map.duration_us / 1_000_000:.2f}s</div></div>
  <div class="card"><div class="muted">Analysis regions</div><div class="value">{len(semantic_map.regions)}</div></div>
  <div class="card"><div class="muted">Raw observations</div><div class="value">{len(semantic_map.observations)}</div></div>
  <div class="card"><div class="muted">Explicit conflicts</div><div class="value">{len(semantic_map.conflicts)}</div></div>
</div>
<section><h2>Timeline</h2><div class="timeline">{timeline}</div>
<p class="muted">Schema {semantic_map.schema_version} · map {semantic_map.semantic_map_version} · hop {semantic_map.analysis_hop_us / 1000:.0f} ms</p></section>
<div class="grid">
<section><h2>Content coverage</h2><table><thead><tr><th>Label</th><th>Duration</th><th>Share</th></tr></thead><tbody>{label_rows}</tbody></table></section>
<section><h2>Providers</h2><table><thead><tr><th>Provider</th><th>Observations</th></tr></thead><tbody>{provider_rows}</tbody></table></section>
<section><h2>Observation kinds</h2><table><thead><tr><th>Kind</th><th>Count</th></tr></thead><tbody>{kind_rows}</tbody></table></section>
</div>
<section><h2>Warnings and unavailable adapters</h2><ul>{warning_items}</ul>
<p class="muted">Unavailable: {html.escape(", ".join(semantic_map.unavailable_adapters) or "none")}</p></section>
<section class="scroll"><h2>Region evidence</h2>{truncation}<table><thead><tr><th>Start</th><th>End</th><th>Label</th><th>Speech</th><th>Silence</th><th>Music</th><th>Noise</th><th>Rumble</th><th>Hum</th><th>Eligible</th><th>Evidence</th><th>Conflicts</th></tr></thead><tbody>{region_rows}</tbody></table></section>
<p class="muted">Transcript text and local paths are intentionally omitted from this debug report.</p>
</main></body></html>
"""
    path.write_text(document, encoding="utf-8")


def _consolidate_regions(regions: tuple[SemanticRegion, ...]) -> tuple[tuple[int, int, str], ...]:
    consolidated: list[tuple[int, int, str]] = []
    for region in regions:
        if consolidated and consolidated[-1][2] == region.content_label and consolidated[-1][1] == region.start_us:
            previous = consolidated[-1]
            consolidated[-1] = (previous[0], region.end_us, previous[2])
        else:
            consolidated.append((region.start_us, region.end_us, region.content_label))
    return tuple(consolidated)


def _region_row(region: SemanticRegion) -> str:
    return (
        f"<tr><td>{region.start_us / 1_000_000:.3f}</td><td>{region.end_us / 1_000_000:.3f}</td>"
        f"<td>{html.escape(region.content_label)}</td><td>{_probability(region.speech_probability)}</td>"
        f"<td>{_probability(region.silence_probability)}</td>"
        f"<td>{_probability(region.music_probability)}</td><td>{_probability(region.noise_probability)}</td>"
        f"<td>{_probability(region.rumble_probability)}</td><td>{_probability(region.hum_probability)}</td>"
        f"<td>{html.escape(region.processing_eligibility.value)}</td>"
        f"<td>{len(region.observation_ids)}</td><td>{len(region.conflict_ids)}</td></tr>"
    )


def _probability(value: float | None) -> str:
    return "—" if value is None else f"{value:.3f}"
