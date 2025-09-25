export enum WaveformStyle {
  Line = 'Line',
  MirroredLine = 'Mirrored Line',
  Bars = 'Bars',
  Circle = 'Circle',
  Equalizer = 'Equalizer',
  Bricks = 'Bricks',
  Radial = 'Radial',
  Particles = 'Particles',
}

export type LineCap = 'butt' | 'round' | 'square';
export type TextAlign = 'left' | 'center' | 'right';
export type TextPosition = 'top' | 'middle' | 'bottom';

export interface TranscriptCue {
  startTime: number;
  endTime: number;
  text: string;
}

export interface AudioEnhancementOptions {
  adaptiveNoiseReduction: boolean;
  humReduction: boolean;
  speechClarityEQ: boolean;
  dynamicRangeCompression: boolean;
  loudnessNormalization: boolean;
}

export interface CustomizationOptions {
  waveformStyle: WaveformStyle;
  backgroundColor: string;
  waveformColor: string;
  waveformOpacity: number;
  waveformPosition: TextPosition;
  lineWidth: number;
  amplitude: number;
  
  // Line, MirroredLine, Circle, Radial
  lineCap: LineCap;

  // Bars, Equalizer
  barWidth: number;
  barSpacing: number;
  barCount: number;

  // Circle
  circleRadius: number;

  // Bricks
  brickHeight: number;
  brickSpacing: number;
  brickCount: number;

  // Radial
  spokeCount: number;
  innerRadius: number;

  // Particles
  particleCount: number;
  particleSpeed: number;
  particleSize: number;

  // Text & Transcript
  overlayText: string;
  fontFamily: string;
  fontSize: number;
  fontColor: string;
  textAlign: TextAlign;
  textPosition: TextPosition;

  // Audio Enhancement
  audioEnhancement: AudioEnhancementOptions;
}