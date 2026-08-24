from __future__ import annotations

import pytest
from ampersand_contracts import WaveformLevel, WaveformPeaks
from ampersand_engine.waveform import select_studio_waveform_peaks


def test_selects_the_finest_populated_level_inside_the_browser_budget() -> None:
    waveform = _waveform(
        WaveformLevel(samples_per_window=960, windows=_windows(8)),
        WaveformLevel(samples_per_window=1_920, windows=_windows(4)),
        WaveformLevel(samples_per_window=3_840, windows=_windows(2)),
    )

    selected = select_studio_waveform_peaks(waveform, max_samples_per_channel=8)

    assert selected.waveform_id == waveform.waveform_id
    assert selected.source_asset_id == waveform.source_asset_id
    assert len(selected.levels) == 1
    assert selected.levels[0].samples_per_window == 1_920
    assert len(selected.levels[0].windows) * 2 == 8


def test_falls_back_to_the_coarsest_level_and_rejects_an_empty_pyramid() -> None:
    waveform = _waveform(
        WaveformLevel(samples_per_window=960, windows=_windows(8)),
        WaveformLevel(samples_per_window=1_920, windows=_windows(4)),
    )
    selected = select_studio_waveform_peaks(waveform, max_samples_per_channel=2)
    assert selected.levels[0].samples_per_window == 1_920

    empty = _waveform(WaveformLevel(samples_per_window=960, windows=()))
    with pytest.raises(ValueError, match="populated level"):
        select_studio_waveform_peaks(empty)
    with pytest.raises(ValueError, match="at least two"):
        select_studio_waveform_peaks(waveform, max_samples_per_channel=1)


def _waveform(*levels: WaveformLevel) -> WaveformPeaks:
    return WaveformPeaks(
        waveform_id="waveform:test",
        source_asset_id="asset:test",
        sample_rate_hz=48_000,
        duration_us=10_000_000,
        channels=1,
        levels=levels,
    )


def _windows(count: int) -> tuple[tuple[tuple[float, float], ...], ...]:
    return tuple(((-0.5, 0.5),) for _ in range(count))
