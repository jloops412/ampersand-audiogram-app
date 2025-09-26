export enum WaveformStyle {
    Line = 'Line',
    MirroredLine = 'Mirrored Line',
    Bars = 'Bars',
    Equalizer = 'Equalizer',
    Circle = 'Circle',
    Bricks = 'Bricks',
    Radial = 'Radial',
    Particles = 'Particles',
}

export interface CustomizationOptions {
    // Auphonic Enhancement
    enhanceWithAuphonic: boolean;
    generateTranscript: boolean;

    // Background
    backgroundColor: string;

    // Waveform
    waveformStyle: WaveformStyle;
    waveformColor: string;
    waveformOpacity: number;
    waveformPosition: 'top' | 'middle' | 'bottom';
    amplitude: number;

    // Line style options
    lineWidth: number;
    lineCap: 'butt' | 'round' | 'square';

    // Bar style options
    barWidth: number;
    barSpacing: number;
    barCount: number;

    // Circle style options
    circleRadius: number;
    
    // Bricks style options
    brickHeight: number;
    brickSpacing: number;
    brickCount: number;
    
    // Radial style options
    spokeCount: number;
    innerRadius: number;

    // Particle style options
    particleCount: number;
    particleSize: number;
    particleSpeed: number;

    // Text Overlay
    overlayText: string;
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

// For Auphonic service
export interface AuphonicPreset {
    uuid: string;
    preset_name: string;
}
