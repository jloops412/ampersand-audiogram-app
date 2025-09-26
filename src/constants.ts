
import { CustomizationOptions, WaveformStyle } from './types';

export const CANVAS_WIDTH = 1080;
export const CANVAS_HEIGHT = 1080;

export const DEFAULT_OPTIONS: CustomizationOptions = {
  backgroundColor: '#1a1a1a',
  
  waveformStyle: WaveformStyle.Bars,
  waveformPosition: 'middle',
  waveformColor: '#ffffff',
  waveformOpacity: 0.8,
  amplitude: 150,
  
  lineWidth: 4,
  lineCap: 'round',

  barWidth: 8,
  barSpacing: 4,
  barCount: 60,

  brickHeight: 10,
  brickSpacing: 4,
  brickCount: 60,

  circleRadius: 200,

  innerRadius: 100,
  spokeCount: 180,

  particleCount: 500,
  particleSize: 2,
  particleSpeed: 2,

  overlayText: 'Your audiogram text goes here',
  fontFamily: 'Inter, sans-serif',
  fontSize: 72,
  fontColor: '#ffffff',
  textAlign: 'center',
  textPosition: 'middle',

  enhanceWithAuphonic: false,
  generateTranscript: false,
};
