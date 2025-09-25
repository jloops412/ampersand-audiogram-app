import React, { forwardRef, useImperativeHandle, useRef, useEffect } from 'react';
import type { CustomizationOptions, TranscriptCue } from '../types';
import { WaveformStyle } from '../types';
import { getStaticPeaks } from '../services/audioService';
import { CANVAS_WIDTH, CANVAS_HEIGHT } from '../constants';

interface PreviewProps {
  audioBuffer: AudioBuffer | null;
  backgroundImageUrl: string | null;
  options: CustomizationOptions;
  transcriptCues: TranscriptCue[] | null;
}

// Helper to convert hex color to rgba
function hexToRgba(hex: string, alpha: number): string {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// Helper to draw wrapped text on canvas
function drawWrappedText(
    ctx: CanvasRenderingContext2D, 
    text: string, 
    x: number, 
    y: number, 
    maxWidth: number, 
    lineHeight: number
) {
    const words = text.split(' ');
    let line = '';
    const lines = [];

    for (let n = 0; n < words.length; n++) {
        const testLine = line + words[n] + ' ';
        const metrics = ctx.measureText(testLine);
        const testWidth = metrics.width;
        if (testWidth > maxWidth && n > 0) {
            lines.push(line);
            line = words[n] + ' ';
        } else {
            line = testLine;
        }
    }
    lines.push(line);
    
    // Adjust y position for vertical alignment
    let startY = y;
    if (ctx.textBaseline === 'middle') {
      startY -= ((lines.length - 1) * lineHeight) / 2;
    } else if (ctx.textBaseline === 'bottom') {
      startY -= (lines.length - 1) * lineHeight;
    }

    lines.forEach((l, i) => {
        ctx.fillText(l.trim(), x, startY + (i * lineHeight));
    });
}

export const Preview = forwardRef<HTMLCanvasElement, PreviewProps>(({
  audioBuffer,
  backgroundImageUrl,
  options,
  transcriptCues,
}, ref) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useImperativeHandle(ref, () => canvasRef.current!);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Static preview rendering
    const staticPeaks = audioBuffer ? getStaticPeaks(audioBuffer, canvas.width / 2) : [];

    const bgImage = new Image();
    bgImage.crossOrigin = "anonymous";
    let isBgImageLoaded = false;
    
    const draw = async () => {
        // Ensure fonts are loaded before drawing text
        await document.fonts.load(`${options.fontSize}px "${options.fontFamily}"`);

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw background color
        ctx.fillStyle = options.backgroundColor;
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Draw background image
        if (backgroundImageUrl && isBgImageLoaded) {
            ctx.drawImage(bgImage, 0, 0, canvas.width, canvas.height);
        }

        // Draw Waveform
        if (audioBuffer) {
            const waveformRgbaColor = hexToRgba(options.waveformColor, options.waveformOpacity);
            ctx.fillStyle = waveformRgbaColor;
            ctx.strokeStyle = waveformRgbaColor;
            ctx.lineCap = options.lineCap;

            const centerX = canvas.width / 2;
            let centerY;

            switch (options.waveformPosition) {
                case 'top':
                    centerY = canvas.height * 0.25;
                    break;
                case 'bottom':
                    centerY = canvas.height * 0.75;
                    break;
                default:
                    centerY = canvas.height / 2;
            }
            
            // For styles not affected by position, override centerY
            if ([WaveformStyle.Circle, WaveformStyle.Radial, WaveformStyle.Particles, WaveformStyle.Equalizer].includes(options.waveformStyle)) {
                 centerY = canvas.height / 2;
            }
            
            // Static waveform drawing logic
            switch (options.waveformStyle) {
                case WaveformStyle.Line: 
                case WaveformStyle.MirroredLine: {
                     ctx.lineWidth = options.lineWidth;
                     // Top half
                     ctx.beginPath();
                     ctx.moveTo(0, centerY);
                     for (let i = 0; i < staticPeaks.length; i++) {
                         const x = (i / staticPeaks.length) * canvas.width;
                         const height = staticPeaks[i] * options.amplitude;
                         ctx.lineTo(x, centerY - height);
                     }
                     ctx.stroke();

                     if (options.waveformStyle === WaveformStyle.MirroredLine) {
                         // Bottom half
                         ctx.beginPath();
                         ctx.moveTo(0, centerY);
                         for (let i = 0; i < staticPeaks.length; i++) {
                             const x = (i / staticPeaks.length) * canvas.width;
                             const height = staticPeaks[i] * options.amplitude;
                             ctx.lineTo(x, centerY + height);
                         }
                         ctx.stroke();
                     }
                     break;
                }
                case WaveformStyle.Bars:
                case WaveformStyle.Equalizer:
                    const barPlusSpacing = options.barWidth + options.barSpacing;
                    const totalBarWidth = options.barCount * barPlusSpacing;
                    const startX = centerX - totalBarWidth / 2;
                    
                    for (let i = 0; i < options.barCount; i++) {
                        const peakIndex = Math.floor((i / options.barCount) * staticPeaks.length);
                        const height = (staticPeaks[peakIndex] || 0) * options.amplitude * 2.5;
                        const x = startX + i * barPlusSpacing;

                        if (options.waveformStyle === WaveformStyle.Bars) {
                            ctx.fillRect(x, centerY - height / 2, options.barWidth, height);
                        } else { // Equalizer
                            ctx.fillRect(x, canvas.height - height, options.barWidth, height);
                        }
                    }
                    break;
                case WaveformStyle.Circle:
                    ctx.lineWidth = options.lineWidth;
                    const points = 360;
                    const peakPoints = Math.floor(staticPeaks.length / 2);
                    for (let i = 0; i < points; i++) {
                        const mirrorI = i > 180 ? 360 - i : i; // Symmetrical
                        const peakIndex = Math.floor((mirrorI / 180) * peakPoints);
                        const amplitude = (staticPeaks[peakIndex] || 0) * options.amplitude;
                        const angle = (i - 90) * (Math.PI / 180);
                        const x1 = centerX + options.circleRadius * Math.cos(angle);
                        const y1 = centerY + options.circleRadius * Math.sin(angle);
                        const x2 = centerX + (options.circleRadius + amplitude) * Math.cos(angle);
                        const y2 = centerY + (options.circleRadius + amplitude) * Math.sin(angle);
                        ctx.beginPath();
                        ctx.moveTo(x1, y1);
                        ctx.lineTo(x2, y2);
                        ctx.stroke();
                    }
                    break;
                case WaveformStyle.Bricks:
                    const brickFullHeight = options.brickHeight + options.brickSpacing;
                    const totalBrickWidth = options.brickCount * brickFullHeight;
                    const brickStartX = centerX - totalBrickWidth / 2;
                    for (let i = 0; i < options.brickCount; i++) {
                        const peakIndex = Math.floor((i / options.brickCount) * staticPeaks.length);
                        const peakHeight = (staticPeaks[peakIndex] || 0) * options.amplitude * 1.5;
                        const numBricks = Math.floor(peakHeight / brickFullHeight);
                        const x = brickStartX + i * brickFullHeight;
                        for (let j = 0; j < numBricks; j++) {
                            const y = centerY - (j * brickFullHeight) - brickFullHeight/2;
                            ctx.fillRect(x, y, brickFullHeight - options.brickSpacing, options.brickHeight);
                        }
                    }
                    break;
                case WaveformStyle.Radial:
                    ctx.lineWidth = options.lineWidth;
                    const peakCount = Math.floor(staticPeaks.length / 2);
                    for (let i = 0; i < options.spokeCount; i++) {
                        const angle = (i / options.spokeCount) * Math.PI * 2;
                        const symmI = Math.abs((i % (options.spokeCount / 2)) - (options.spokeCount / 4));
                        const peakIndex = Math.floor((symmI / (options.spokeCount / 4)) * peakCount);
                        const amplitude = (staticPeaks[peakIndex] || 0) * options.amplitude;
                        
                        const x1 = centerX + options.innerRadius * Math.cos(angle);
                        const y1 = centerY + options.innerRadius * Math.sin(angle);
                        const x2 = centerX + (options.innerRadius + amplitude) * Math.cos(angle);
                        const y2 = centerY + (options.innerRadius + amplitude) * Math.sin(angle);
                        
                        ctx.beginPath();
                        ctx.moveTo(x1, y1);
                        ctx.lineTo(x2, y2);
                        ctx.stroke();
                    }
                    break;
                case WaveformStyle.Particles:
                    // Static preview for particles: a snapshot
                    for(let i=0; i < options.particleCount / 5; i++) {
                        const angle = Math.random() * Math.PI * 2;
                        const peakIndex = Math.floor(Math.random() * staticPeaks.length);
                        const distance = (staticPeaks[peakIndex] || 0) * options.amplitude * 1.5;
                        const x = centerX + Math.cos(angle) * distance;
                        const y = centerY + Math.sin(angle) * distance;
                        ctx.beginPath();
                        ctx.arc(x, y, options.particleSize, 0, Math.PI * 2);
                        ctx.fill();
                    }
                    break;
            }
        }

        // Draw Text
        const textToDraw = options.overlayText || (transcriptCues && transcriptCues.length > 0 ? transcriptCues[0].text : '');
        if (textToDraw) {
            ctx.fillStyle = options.fontColor;
            ctx.font = `${options.fontSize}px "${options.fontFamily}"`;
            ctx.textAlign = options.textAlign;

            const padding = 60;
            let x: number;
            if (options.textAlign === 'left') x = padding;
            else if (options.textAlign === 'right') x = canvas.width - padding;
            else x = canvas.width / 2;

            let y: number;
            if (options.textPosition === 'top') {
                y = padding;
                ctx.textBaseline = 'top';
            } else if (options.textPosition === 'bottom') {
                y = canvas.height - padding;
                ctx.textBaseline = 'bottom';
            } else { // middle
                y = canvas.height / 2;
                ctx.textBaseline = 'middle';
            }

            const maxWidth = canvas.width - (padding * 2);
            const lineHeight = options.fontSize * 1.2;
            drawWrappedText(ctx, textToDraw, x, y, maxWidth, lineHeight);
        }
    };

    if (backgroundImageUrl) {
        bgImage.onload = () => {
            isBgImageLoaded = true;
            draw();
        };
        bgImage.src = backgroundImageUrl;
    } else {
        draw();
    }
    
  }, [audioBuffer, backgroundImageUrl, options, transcriptCues]);

  return (
    <canvas
      ref={canvasRef}
      width={CANVAS_WIDTH}
      height={CANVAS_HEIGHT}
      className="w-full h-full object-contain"
    />
  );
});