
import type { CustomizationOptions } from './types';
import { WaveformStyle } from './types';

export const CANVAS_WIDTH = 1920;
export const CANVAS_HEIGHT = 1080;

export const DEFAULT_OPTIONS: CustomizationOptions = {
  // General
  backgroundColor: '#1a1a1a',
  overlayText: 'Your audiogram text goes here.',

  // Waveform
  waveformStyle: WaveformStyle.MirroredLine,
  waveformColor: '#ffffff',
  waveformOpacity: 0.85,
  waveformPosition: 'middle',
  amplitude: 100,

  // Line/Mirrored Line specific
  lineWidth: 4,
  lineCap: 'round',

  // Bars/Equalizer specific
  barWidth: 8,
  barSpacing: 4,
  barCount: 128,

  // Circle specific
  circleRadius: 200,

  // Bricks specific
  brickHeight: 10,
  brickSpacing: 2,
  brickCount: 80,

  // Radial specific
  innerRadius: 150,
  spokeCount: 180,

  // Particles specific
  particleCount: 1000,
  particleSize: 2,
  particleSpeed: 2,

  // Text
  fontColor: '#ffffff',
  fontSize: 72,
  fontFamily: 'Inter, sans-serif',
  textAlign: 'center',
  textPosition: 'middle',
};
