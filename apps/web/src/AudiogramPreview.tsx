import { useEffect, useState } from 'react';

import type { AudiogramSettings } from './types';

const PEAKS = [22, 46, 34, 62, 81, 55, 39, 73, 91, 66, 48, 78, 58, 88, 43, 69, 96, 61, 35, 76, 52, 84, 64, 41];

export function AudiogramPreview({
  settings,
  media,
  title,
}: {
  settings: AudiogramSettings;
  media: File | null;
  title: string;
}) {
  const [mediaUrl, setMediaUrl] = useState('');

  useEffect(() => {
    if (!media) {
      setMediaUrl('');
      return;
    }
    const next = URL.createObjectURL(media);
    setMediaUrl(next);
    return () => URL.revokeObjectURL(next);
  }, [media]);

  const ratio = {
    square: '1 / 1',
    feed_portrait: '4 / 5',
    portrait: '9 / 16',
    landscape: '16 / 9',
  }[settings.aspect_ratio];
  const headline = settings.headline.trim() || title.trim() || 'Your production title';
  const position = { top: '31%', center: '50%', bottom: '76%' }[settings.waveform_position];
  const copyPosition = { top: '11%', center: '39%', bottom: '69%' }[settings.text_position];
  const background = {
    color: settings.background_color,
    gradient: `linear-gradient(145deg, ${settings.background_color}, ${settings.accent_color})`,
    radial: `radial-gradient(circle at 50% 40%, ${settings.accent_color}, ${settings.background_color} 68%)`,
    artwork: settings.background_color,
    video: settings.background_color,
  }[settings.background_mode];
  const fontFamily = {
    sans: 'Inter, ui-sans-serif, system-ui, sans-serif',
    serif: 'Georgia, Cambria, Times New Roman, serif',
    mono: 'ui-monospace, SFMono-Regular, Consolas, monospace',
  }[settings.font_family];

  return (
    <div className="audiogram-preview-shell">
      <div
        className={`audiogram-preview background-${settings.background_mode}`}
        style={{ aspectRatio: ratio, background, color: settings.text_color }}
      >
        {mediaUrl && settings.background_mode === 'artwork' && (
          <img
            src={mediaUrl}
            alt="Selected audiogram background preview"
            style={{
              objectFit: settings.background_fit,
              filter: `blur(${settings.background_blur * 0.45}px)`,
              transform: settings.background_blur ? 'scale(1.045)' : undefined,
            }}
          />
        )}
        {mediaUrl && settings.background_mode === 'video' && (
          <video
            src={mediaUrl}
            muted
            loop
            autoPlay
            playsInline
            style={{
              objectFit: settings.background_fit,
              filter: `blur(${settings.background_blur * 0.45}px)`,
              transform: settings.background_blur ? 'scale(1.045)' : undefined,
            }}
          />
        )}
        <span className="preview-dim" style={{ background: `rgba(0,0,0,${settings.background_dim})` }} />
        <span
          className="preview-vignette"
          style={{ opacity: settings.background_vignette }}
        />
        <div
          className={`preview-copy align-${settings.text_align} panel-${settings.text_panel}`}
          style={{
            top: copyPosition,
            textAlign: settings.text_align,
            fontFamily,
            borderColor: settings.accent_color,
            backgroundColor: settings.text_panel === 'accent' ? `${settings.accent_color}d9` : undefined,
          }}
        >
          <strong style={{ fontSize: `${settings.headline_size_percent}cqw` }}>{headline}</strong>
          {settings.subtitle && (
            <small style={{ fontSize: `${settings.subtitle_size_percent}cqw`, color: settings.accent_color }}>
              {settings.subtitle}
            </small>
          )}
        </div>
        <div
          className={`preview-waveform style-${settings.waveform_style} frame-${settings.waveform_frame}`}
          style={{
            top: position,
            width: `${settings.waveform_width_percent}%`,
            height: `${settings.waveform_height_percent}%`,
            color: settings.waveform_color,
            opacity: settings.waveform_opacity,
            borderColor: settings.accent_color,
            backgroundColor:
              settings.waveform_frame === 'accent'
                ? `${settings.accent_color}33`
                : settings.waveform_frame === 'glass'
                  ? '#03070852'
                  : undefined,
            filter: settings.waveform_glow
              ? `drop-shadow(0 0 ${2 + settings.waveform_glow * 16}px ${settings.waveform_color})`
              : undefined,
          }}
        >
          {PEAKS.map((peak, index) => (
            <i
              key={index}
              style={{
                height: `${peak}%`,
                animationDelay: `${index * -0.047}s`,
                animationDuration: `${0.76 + (index % 5) * 0.11}s`,
              }}
            />
          ))}
        </div>
      </div>
      <small>Animated layout preview · the server renders the final visualizer from mastered audio.</small>
    </div>
  );
}
