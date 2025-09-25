import { WaveformStyle } from './types';
import type { CustomizationOptions } from './types';

export const GOOGLE_FONTS = [
  'Montserrat',
  'Lato',
  'Playfair Display',
  'Roboto Mono',
  'Lobster',
];

export const DEFAULT_OPTIONS: CustomizationOptions = {
  waveformStyle: WaveformStyle.Line,
  backgroundColor: '#1a1b20',
  waveformColor: '#D7B185',
  waveformOpacity: 1.0,
  waveformPosition: 'middle',
  lineWidth: 3,
  amplitude: 150,
  
  // Line, MirroredLine, Circle, Radial
  lineCap: 'round',

  // Bars, Equalizer
  barWidth: 5,
  barSpacing: 2,
  barCount: 128,

  // Circle
  circleRadius: 150,

  // Bricks
  brickHeight: 8,
  brickSpacing: 4,
  brickCount: 80,

  // Radial
  spokeCount: 180,
  innerRadius: 50,
  
  // Particles
  particleCount: 200,
  particleSpeed: 1.5,
  particleSize: 3,
  
  // Audio Enhancement
  audioEnhancement: {
    adaptiveNoiseReduction: false,
    humReduction: false,
    speechClarityEQ: false,
    dynamicRangeCompression: false,
    loudnessNormalization: false,
  },

  // Text & Transcript
  overlayText: '',
  fontFamily: GOOGLE_FONTS[0],
  fontSize: 80,
  fontColor: '#ffffff',
  textAlign: 'center',
  textPosition: 'middle',
};

export const CANVAS_WIDTH = 1920;
export const CANVAS_HEIGHT = 1080;