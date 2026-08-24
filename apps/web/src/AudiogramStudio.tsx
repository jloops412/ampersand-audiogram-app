import { useRef } from 'react';

import {
  AUDIOGRAM_VISUAL_PRESETS,
  applyAudiogramPreset,
  matchesAudiogramPreset,
} from './audiogramPresets';
import { AudiogramPreview } from './AudiogramPreview';
import type { AudiogramSettings } from './types';

const VISUALIZER_LABELS: Array<{
  value: AudiogramSettings['waveform_style'];
  label: string;
  description: string;
}> = [
  { value: 'mirrored', label: 'Mirror', description: 'Centered voice energy' },
  { value: 'line', label: 'Line', description: 'Fine minimal motion' },
  { value: 'bars', label: 'Bars', description: 'Bold audio columns' },
  { value: 'dots', label: 'Particles', description: 'Light point motion' },
  { value: 'spectrum', label: 'Spectrum', description: 'Frequency analyzer' },
  { value: 'spectrum_dots', label: 'Frequency dots', description: 'Modern dotted analyzer' },
];

function presetBackground(mode: AudiogramSettings['background_mode'], base: string, accent: string) {
  if (mode === 'radial') return `radial-gradient(circle at 50% 42%, ${accent}, ${base} 64%)`;
  if (mode === 'gradient') return `linear-gradient(145deg, ${base}, ${accent})`;
  return base;
}

export function AudiogramStudio({
  settings,
  media,
  title,
  maxMediaLabel,
  onChange,
  onMediaChange,
}: {
  settings: AudiogramSettings;
  media: File | null;
  title: string;
  maxMediaLabel: string;
  onChange: (settings: AudiogramSettings) => void;
  onMediaChange: (media: File | null) => void;
}) {
  const mediaInputRef = useRef<HTMLInputElement>(null);
  const set = <Key extends keyof AudiogramSettings>(key: Key, value: AudiogramSettings[Key]) => {
    onChange({ ...settings, spec_version: '1.1', [key]: value });
  };
  const backgroundNeedsMedia = settings.background_mode === 'artwork' || settings.background_mode === 'video';

  return (
    <div className="audiogram-controls">
      <div className="visual-preset-heading">
        <div>
          <strong>Start with a complete look</strong>
          <p>Each look sets real render controls. Customize anything after choosing one.</p>
        </div>
        <span>6 looks</span>
      </div>
      <div className="visual-presets" role="list" aria-label="Audiogram visual looks">
        {AUDIOGRAM_VISUAL_PRESETS.map((preset) => {
          const selected = matchesAudiogramPreset(settings, preset);
          const presetSettings = preset.settings;
          return (
            <button
              key={preset.id}
              type="button"
              className={`visual-preset ${selected ? 'selected' : ''}`}
              onClick={() => onChange(applyAudiogramPreset(settings, preset))}
              aria-pressed={selected}
            >
              <span
                className="visual-preset-art"
                style={{
                  background: presetBackground(
                    presetSettings.background_mode || 'color',
                    presetSettings.background_color || '#111718',
                    presetSettings.accent_color || '#e1b977',
                  ),
                  color: presetSettings.waveform_color,
                }}
              >
                <i className="preset-title-line" style={{ background: presetSettings.text_color }} />
                <i className="preset-subtitle-line" style={{ background: presetSettings.accent_color }} />
                <span className={`preset-wave style-${presetSettings.waveform_style || 'mirrored'}`}>
                  {[28, 64, 42, 82, 55, 94, 48, 72, 36, 88, 58, 76].map((height, index) => (
                    <b key={index} style={{ height: `${height}%` }} />
                  ))}
                </span>
              </span>
              <span className="visual-preset-copy">
                <strong>{preset.name}</strong>
                <small>{preset.description}</small>
              </span>
            </button>
          );
        })}
      </div>

      <div className="audiogram-workbench">
        <AudiogramPreview settings={settings} media={media} title={title} />
        <div className="audiogram-essentials">
          <label className="select-control">
            <span>Canvas</span>
            <select
              value={settings.aspect_ratio}
              onChange={(event) => set('aspect_ratio', event.target.value as AudiogramSettings['aspect_ratio'])}
            >
              <option value="square">Square · 1:1 · 1080×1080</option>
              <option value="feed_portrait">Feed portrait · 4:5 · 1080×1350</option>
              <option value="portrait">Story / reel · 9:16 · 1080×1920</option>
              <option value="landscape">Landscape · 16:9 · 1920×1080</option>
            </select>
          </label>
          <fieldset className="choice-fieldset">
            <legend>Background</legend>
            <div className="choice-pills">
              {([
                ['gradient', 'Gradient'],
                ['radial', 'Radial'],
                ['color', 'Solid'],
                ['artwork', 'Image'],
                ['video', 'Video'],
              ] as const).map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  className={settings.background_mode === value ? 'selected' : ''}
                  onClick={() => set('background_mode', value)}
                  aria-pressed={settings.background_mode === value}
                >
                  {label}
                </button>
              ))}
            </div>
          </fieldset>
          {backgroundNeedsMedia && (
            <div className="artwork-picker">
              <input
                ref={mediaInputRef}
                type="file"
                accept={
                  settings.background_mode === 'video'
                    ? 'video/mp4,video/quicktime,video/webm,.m4v'
                    : 'image/jpeg,image/png,image/webp'
                }
                hidden
                onChange={(event) => onMediaChange(event.target.files?.[0] || null)}
              />
              <button type="button" className="button button-secondary" onClick={() => mediaInputRef.current?.click()}>
                {media ? 'Replace background' : `Choose ${settings.background_mode === 'video' ? 'video' : 'image'}`}
              </button>
              <span>
                {media
                  ? media.name
                  : `${settings.background_mode === 'video' ? 'MP4, MOV, M4V, or WebM' : 'JPG, PNG, or WebP'} · up to ${maxMediaLabel}`}
              </span>
            </div>
          )}
          <div className="palette-row">
            <label>
              <input
                type="color"
                value={settings.background_color}
                onChange={(event) => set('background_color', event.target.value)}
              />
              <span>Base</span>
            </label>
            <label>
              <input
                type="color"
                value={settings.accent_color}
                onChange={(event) => set('accent_color', event.target.value)}
              />
              <span>Accent</span>
            </label>
            <label>
              <input
                type="color"
                value={settings.waveform_color}
                onChange={(event) => set('waveform_color', event.target.value)}
              />
              <span>Visualizer</span>
            </label>
            <label>
              <input
                type="color"
                value={settings.text_color}
                onChange={(event) => set('text_color', event.target.value)}
              />
              <span>Type</span>
            </label>
          </div>
        </div>
      </div>

      <div className="visualizer-heading">
        <div>
          <strong>Visualizer</strong>
          <p>Waveform and frequency-driven modes render from the mastered audio.</p>
        </div>
      </div>
      <div className="visualizer-grid">
        {VISUALIZER_LABELS.map((visualizer) => (
          <button
            key={visualizer.value}
            type="button"
            className={settings.waveform_style === visualizer.value ? 'selected' : ''}
            onClick={() => set('waveform_style', visualizer.value)}
            aria-pressed={settings.waveform_style === visualizer.value}
          >
            <span className={`visualizer-glyph style-${visualizer.value}`} aria-hidden="true">
              {[32, 68, 48, 90, 58, 78, 42, 72].map((height, index) => (
                <i key={index} style={{ height: `${height}%` }} />
              ))}
            </span>
            <strong>{visualizer.label}</strong>
            <small>{visualizer.description}</small>
          </button>
        ))}
      </div>

      <div className="metadata-grid audiogram-copy-fields">
        <label>
          <span>Headline override</span>
          <input
            className="text-input"
            value={settings.headline}
            onChange={(event) => set('headline', event.target.value)}
            placeholder="Uses production title when blank"
          />
        </label>
        <label>
          <span>Subtitle</span>
          <input
            className="text-input"
            value={settings.subtitle}
            onChange={(event) => set('subtitle', event.target.value)}
            placeholder="Show, speaker, or call to action"
          />
        </label>
      </div>

      <details className="advanced-controls audiogram-advanced">
        <summary>Fine-tune layout, effects &amp; render</summary>
        <div className="three-up compact-selects">
          <label className="select-card">
            <span>Amplitude response</span>
            <select
              value={settings.waveform_scale}
              onChange={(event) => set('waveform_scale', event.target.value as AudiogramSettings['waveform_scale'])}
            >
              <option value="linear">Linear · literal</option>
              <option value="sqrt">Square root · balanced</option>
              <option value="cbrt">Cube root · fuller</option>
              <option value="log">Logarithmic · energetic</option>
            </select>
          </label>
          <label className="select-card">
            <span>Visualizer position</span>
            <select
              value={settings.waveform_position}
              onChange={(event) => set('waveform_position', event.target.value as AudiogramSettings['waveform_position'])}
            >
              <option value="top">Upper</option>
              <option value="center">Center</option>
              <option value="bottom">Lower</option>
            </select>
          </label>
          <label className="select-card">
            <span>Visualizer plate</span>
            <select
              value={settings.waveform_frame}
              onChange={(event) => set('waveform_frame', event.target.value as AudiogramSettings['waveform_frame'])}
            >
              <option value="none">None</option>
              <option value="glass">Glass panel</option>
              <option value="outline">Accent outline</option>
              <option value="accent">Accent wash</option>
            </select>
          </label>
          <label className="select-card">
            <span>Typeface</span>
            <select
              value={settings.font_family}
              onChange={(event) => set('font_family', event.target.value as AudiogramSettings['font_family'])}
            >
              <option value="sans">Modern sans</option>
              <option value="serif">Editorial serif</option>
              <option value="mono">Studio mono</option>
            </select>
          </label>
          <label className="select-card">
            <span>Text position</span>
            <select
              value={settings.text_position}
              onChange={(event) => set('text_position', event.target.value as AudiogramSettings['text_position'])}
            >
              <option value="top">Upper</option>
              <option value="center">Center</option>
              <option value="bottom">Lower</option>
            </select>
          </label>
          <label className="select-card">
            <span>Text treatment</span>
            <select
              value={settings.text_panel}
              onChange={(event) => set('text_panel', event.target.value as AudiogramSettings['text_panel'])}
            >
              <option value="none">Clean</option>
              <option value="shadow">Soft shadow</option>
              <option value="glass">Glass box</option>
              <option value="accent">Accent box</option>
            </select>
          </label>
          <label className="select-card">
            <span>Text alignment</span>
            <select
              value={settings.text_align}
              onChange={(event) => set('text_align', event.target.value as AudiogramSettings['text_align'])}
            >
              <option value="left">Left</option>
              <option value="center">Center</option>
              <option value="right">Right</option>
            </select>
          </label>
          <label className="select-card">
            <span>Background fit</span>
            <select
              value={settings.background_fit}
              onChange={(event) => set('background_fit', event.target.value as AudiogramSettings['background_fit'])}
            >
              <option value="cover">Cover · fill canvas</option>
              <option value="contain">Contain · show all</option>
            </select>
          </label>
          <label className="select-card">
            <span>Frame rate</span>
            <select
              value={settings.frame_rate}
              onChange={(event) => set('frame_rate', Number(event.target.value) as 24 | 30 | 60)}
            >
              <option value="24">24 fps · cinematic</option>
              <option value="30">30 fps · standard</option>
              <option value="60">60 fps · smooth / large</option>
            </select>
          </label>
          <label className="select-card">
            <span>Render quality</span>
            <select
              value={settings.render_quality}
              onChange={(event) => set('render_quality', event.target.value as AudiogramSettings['render_quality'])}
            >
              <option value="draft">Draft · quick review</option>
              <option value="standard">Standard · recommended</option>
              <option value="high">High · slower / larger</option>
            </select>
          </label>
        </div>
        <div className="control-stack">
          <RangeControl label="Visualizer width" hint="Percentage of canvas width" value={settings.waveform_width_percent} min={40} max={100} step={1} suffix="%" onChange={(value) => set('waveform_width_percent', value)} />
          <RangeControl label="Visualizer height" hint="Percentage of canvas height" value={settings.waveform_height_percent} min={10} max={60} step={1} suffix="%" onChange={(value) => set('waveform_height_percent', value)} />
          <RangeControl label="Visualizer opacity" hint="Blend with the artwork" value={settings.waveform_opacity * 100} min={10} max={100} step={5} suffix="%" onChange={(value) => set('waveform_opacity', value / 100)} />
          <RangeControl label="Glow" hint="Luminous halo around the visualizer" value={settings.waveform_glow * 100} min={0} max={100} step={5} suffix="%" onChange={(value) => set('waveform_glow', value / 100)} />
          <RangeControl label="Background dim" hint="Darkens media for contrast" value={settings.background_dim * 100} min={0} max={85} step={5} suffix="%" onChange={(value) => set('background_dim', value / 100)} />
          <RangeControl label="Background blur" hint="Softens detail behind the copy" value={settings.background_blur} min={0} max={30} step={1} suffix=" px" onChange={(value) => set('background_blur', value)} />
          <RangeControl label="Vignette" hint="Adds cinematic edge depth" value={settings.background_vignette * 100} min={0} max={100} step={5} suffix="%" onChange={(value) => set('background_vignette', value / 100)} />
          <RangeControl label="Headline size" hint="Percentage of canvas width" value={settings.headline_size_percent} min={2} max={10} step={0.1} suffix="%" decimals={1} onChange={(value) => set('headline_size_percent', value)} />
          <RangeControl label="Subtitle size" hint="Percentage of canvas width" value={settings.subtitle_size_percent} min={1} max={6} step={0.1} suffix="%" decimals={1} onChange={(value) => set('subtitle_size_percent', value)} />
        </div>
      </details>
    </div>
  );
}

function RangeControl({
  label,
  hint,
  value,
  min,
  max,
  step,
  suffix,
  decimals = 0,
  onChange,
}: {
  label: string;
  hint: string;
  value: number;
  min: number;
  max: number;
  step: number;
  suffix: string;
  decimals?: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="range-control">
      <span><strong>{label}</strong><small>{hint}</small></span>
      <input type="range" min={min} max={max} step={step} value={value} onChange={(event) => onChange(Number(event.target.value))} />
      <output>{value.toFixed(decimals)}{suffix}</output>
    </label>
  );
}
