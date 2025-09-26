
export enum WaveformStyle {
  Line = 'line',
  MirroredLine = 'mirrored-line',
  Bars = 'bars',
  Equalizer = 'equalizer',
  Circle = 'circle',
  Bricks = 'bricks',
  Radial = 'radial',
  Particles = 'particles',
}

export interface TranscriptCue {
  startTime: number;
  endTime: number;
  text: string;
}

export interface CustomizationOptions {
  // Waveform
  waveformStyle: WaveformStyle;
  waveformColor: string;
  waveformOpacity: number;
  waveformPosition: 'top' | 'middle' | 'bottom';
  amplitude: number;
  
  // Line / Mirrored Line
  lineWidth: number;
  lineCap: 'butt' | 'round' | 'square';

  // Bars / Equalizer
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
  particleSize: number;
  particleSpeed: number;

  // Text
  overlayText: string;
  fontFamily: string;
  fontSize: number;
  fontColor: string;
  textAlign: 'left' | 'center' | 'right';
  textPosition: 'top' | 'middle' | 'bottom';
  
  // Background
  backgroundColor: string;
}
