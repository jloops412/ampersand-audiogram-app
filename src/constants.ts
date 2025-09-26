import { CustomizationOptions, WaveformStyle } from './types';

export const CANVAS_WIDTH = 1280;
export const CANVAS_HEIGHT = 720;

export const DEFAULT_OPTIONS: CustomizationOptions = {
    // Auphonic
    enhanceWithAuphonic: false,
    generateTranscript: false,

    // Background
    backgroundColor: '#1a1a1a',

    // Waveform
    waveformStyle: WaveformStyle.MirroredLine,
    waveformColor: '#ffffff',
    waveformOpacity: 0.85,
    waveformPosition: 'middle',
    amplitude: 150,

    // Line style options
    lineWidth: 4,
    lineCap: 'round',

    // Bar style options
    barWidth: 5,
    barSpacing: 2,
    barCount: 128,

    // Circle style options
    circleRadius: 100,

    // Bricks style options
    brickHeight: 10,
    brickSpacing: 2,
    brickCount: 80,
    
    // Radial style options
    spokeCount: 180,
    innerRadius: 80,

    // Particle style options
    particleCount: 500,
    particleSize: 2,
    particleSpeed: 1,

    // Text Overlay
    overlayText: 'Audiogram Generator',
    fontColor: '#ffffff',
    fontSize: 64,
    fontFamily: 'Arial',
    textAlign: 'center',
    textPosition: 'middle',
};

export const FONT_FAMILY_OPTIONS = [
    'Lato',
    'Montserrat',
    'Roboto Mono',
    'Playfair Display',
    'Lobster',
    'Arial',
    'Helvetica',
    'Times New Roman',
    'Georgia',
    'Courier New',
    'Verdana',
];
