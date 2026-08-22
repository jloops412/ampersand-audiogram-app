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

  return (
    <div className="audiogram-preview-shell">
      <div
        className="audiogram-preview"
        style={{ aspectRatio: ratio, backgroundColor: settings.background_color, color: settings.text_color }}
      >
        {mediaUrl && settings.background_mode === 'artwork' && (
          <img src={mediaUrl} alt="Selected audiogram background preview" style={{ objectFit: settings.background_fit }} />
        )}
        {mediaUrl && settings.background_mode === 'video' && (
          <video src={mediaUrl} muted loop autoPlay playsInline style={{ objectFit: settings.background_fit }} />
        )}
        <span className="preview-dim" style={{ background: `rgba(0,0,0,${settings.background_dim})` }} />
        <div
          className={`preview-copy align-${settings.text_align}`}
          style={{ textAlign: settings.text_align }}
        >
          <strong style={{ fontSize: `${settings.headline_size_percent * 0.34}cqw` }}>{headline}</strong>
          {settings.subtitle && (
            <small style={{ fontSize: `${settings.subtitle_size_percent * 0.34}cqw` }}>{settings.subtitle}</small>
          )}
        </div>
        <div
          className={`preview-waveform style-${settings.waveform_style}`}
          style={{
            top: position,
            width: `${settings.waveform_width_percent}%`,
            height: `${settings.waveform_height_percent}%`,
            color: settings.waveform_color,
            opacity: settings.waveform_opacity,
          }}
        >
          {PEAKS.map((peak, index) => (
            <i key={index} style={{ height: `${peak}%` }} />
          ))}
        </div>
      </div>
      <small>Live layout preview · the server renders the animated waveform and mastered audio.</small>
    </div>
  );
}
