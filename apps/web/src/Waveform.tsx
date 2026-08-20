import { useEffect, useRef } from 'react';

import type { WaveformPeaks } from './types';

interface WaveformProps {
  waveform: WaveformPeaks | null;
  progress?: number;
}

export function Waveform({ waveform, progress = 0 }: WaveformProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !waveform?.levels.length) return;
    const level = waveform.levels.reduce((best, candidate) => {
      const bestDistance = Math.abs(best.windows.length - 1200);
      const candidateDistance = Math.abs(candidate.windows.length - 1200);
      return candidateDistance < bestDistance ? candidate : best;
    });

    const draw = () => {
      const bounds = canvas.getBoundingClientRect();
      const ratio = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.max(1, Math.round(bounds.width * ratio));
      canvas.height = Math.max(1, Math.round(bounds.height * ratio));
      const context = canvas.getContext('2d');
      if (!context) return;
      context.scale(ratio, ratio);
      const width = bounds.width;
      const height = bounds.height;
      const middle = height / 2;
      context.clearRect(0, 0, width, height);
      context.fillStyle = '#111719';
      context.fillRect(0, 0, width, height);
      context.strokeStyle = 'rgba(255,255,255,.08)';
      context.beginPath();
      context.moveTo(0, middle + 0.5);
      context.lineTo(width, middle + 0.5);
      context.stroke();

      const buckets = Math.max(1, Math.floor(width));
      context.fillStyle = '#d0ad79';
      for (let x = 0; x < buckets; x += 1) {
        const from = Math.floor((x / buckets) * level.windows.length);
        const to = Math.max(from + 1, Math.floor(((x + 1) / buckets) * level.windows.length));
        let minimum = 0;
        let maximum = 0;
        for (let index = from; index < Math.min(to, level.windows.length); index += 1) {
          const channel = level.windows[index]?.[0];
          if (!channel) continue;
          minimum = Math.min(minimum, channel[0]);
          maximum = Math.max(maximum, channel[1]);
        }
        const top = middle - maximum * (middle - 8);
        const bottom = middle - minimum * (middle - 8);
        context.fillRect(x, top, 1, Math.max(1, bottom - top));
      }
      if (progress > 0) {
        context.fillStyle = 'rgba(107, 236, 197, .12)';
        context.fillRect(0, 0, width * Math.min(1, progress), height);
        context.fillStyle = '#6becc5';
        context.fillRect(width * Math.min(1, progress), 0, 1.5, height);
      }
    };

    const observer = new ResizeObserver(draw);
    observer.observe(canvas);
    draw();
    return () => observer.disconnect();
  }, [waveform, progress]);

  return <canvas ref={canvasRef} className="waveform-canvas" aria-label="Precomputed audio waveform" />;
}
