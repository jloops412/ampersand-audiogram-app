
import { CustomizationOptions, WaveformStyle } from './types';

export const CANVAS_WIDTH = 1080;
export const CANVAS_HEIGHT = 1080;

export const DEFAULT_OPTIONS: CustomizationOptions = {
  // Waveform
  waveformStyle: WaveformStyle.Bars,
  waveformColor: '#FFFFFF',
  waveformOpacity: 0.8,
  waveformPosition: 'middle',
  amplitude: 100,

  // Line / Mirrored Line
  lineWidth: 4,
  lineCap: 'round',

  // Bars / Equalizer
  barWidth: 8,
  barSpacing: 4,
  barCount: 64,

  // Circle
  circleRadius: 150,

  // Bricks
  brickHeight: 10,
  brickSpacing: 4,
  brickCount: 64,

  // Radial
  spokeCount: 120,
  innerRadius: 100,
  
  // Particles
  particleCount: 200,
  particleSize: 3,
  particleSpeed: 2,

  // Text
  overlayText: 'Your audiogram text here',
  fontFamily: 'Inter, sans-serif',
  fontSize: 64,
  fontColor: '#FFFFFF',
  textAlign: 'center',
  textPosition: 'middle',
  
  // Background
  backgroundColor: '#1a1a1a',
};
