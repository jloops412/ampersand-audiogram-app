
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

export interface CustomizationOptions {
  // General
  backgroundColor: string;
  overlayText: string;

  // Waveform
  waveformStyle: WaveformStyle;
  waveformColor: string;
  waveformOpacity: number;
  waveformPosition: 'top' | 'middle' | 'bottom';
  amplitude: number;

  // Line/Mirrored Line specific
  lineWidth: number;
  lineCap: 'butt' | 'round' | 'square';

  // Bars/Equalizer specific
  barWidth: number;
  barSpacing: number;
  barCount: number;
  
  // Circle specific
  circleRadius: number;

  // Bricks specific
  brickHeight: number;
  brickSpacing: number;
  brickCount: number;

  // Radial specific
  innerRadius: number;
  spokeCount: number;

  // Particles specific
  particleCount: number;
  particleSize: number;
  particleSpeed: number;

  // Text
  fontColor: string;
  fontSize: number;
  fontFamily: string;
  textAlign: 'left' | 'center' | 'right';
  textPosition: 'top' | 'middle' | 'bottom';
}

export interface TranscriptCue {
  startTime: number;
  endTime: number;
  text: string;
}

export interface AuphonicPreset {
    uuid: string;
    preset_name: string;
}

export interface AuphonicProduction {
    uuid: string;
    status_string: string;
    // other fields as needed
}
