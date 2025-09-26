
export enum WaveformStyle {
  Line = 'Line',
  MirroredLine = 'Mirrored Line',
  Bars = 'Bars',
  Bricks = 'Bricks',
  Circle = 'Circle',
  Radial = 'Radial',
  Particles = 'Particles',
  Equalizer = 'Equalizer',
}

export type WaveformPosition = 'top' | 'middle' | 'bottom';
export type TextPosition = 'top' | 'middle' | 'bottom';
export type TextAlign = 'left' | 'center' | 'right';
export type LineCap = 'butt' | 'round' | 'square';

export interface CustomizationOptions {
  // General
  backgroundColor: string;
  
  // Waveform
  waveformStyle: WaveformStyle;
  waveformPosition: WaveformPosition;
  waveformColor: string;
  waveformOpacity: number;
  amplitude: number;
  
  // Waveform specific: Line / MirroredLine
  lineWidth: number;
  lineCap: LineCap;

  // Waveform specific: Bars
  barWidth: number;
  barSpacing: number;
  barCount: number;

  // Waveform specific: Bricks
  brickHeight: number;
  brickSpacing: number;
  brickCount: number;

  // Waveform specific: Circle
  circleRadius: number;

  // Waveform specific: Radial
  innerRadius: number;
  spokeCount: number;

  // Waveform specific: Particles
  particleCount: number;
  particleSize: number;
  particleSpeed: number;

  // Text
  overlayText: string;
  fontFamily: string;
  fontSize: number;
  fontColor: string;
  textAlign: TextAlign;
  textPosition: TextPosition;

  // Auphonic Enhancement
  enhanceWithAuphonic: boolean;
  generateTranscript: boolean;
}

export interface TranscriptCue {
  startTime: number;
  endTime: number;
  text: string;
}
