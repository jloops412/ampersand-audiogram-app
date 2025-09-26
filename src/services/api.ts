import type { CustomizationOptions, TranscriptCue } from '../types';
import { DEFAULT_OPTIONS, CANVAS_WIDTH, CANVAS_HEIGHT } from '../constants';
import { generateVideo } from './videoService';
import { parseTranscriptFile } from './transcriptService';

export interface CreateAudiogramParams {
  audioFile: File;
  backgroundImageFile?: File | null;
  transcriptFile?: File | null;
  transcriptCues?: TranscriptCue[] | null; // Allow passing pre-parsed cues
  options?: Partial<CustomizationOptions>;
  onProgress?: (progress: number) => void;
}

export async function createAudiogram({
  audioFile,
  backgroundImageFile = null,
  transcriptFile = null,
  transcriptCues = null, // Accept pre-parsed cues
  options = {},
  onProgress = () => {},
}: CreateAudiogramParams): Promise<Blob> {
  if (!audioFile) {
    throw new Error('An audio file is required to create an audiogram.');
  }

  const finalOptions: CustomizationOptions = { 
    ...DEFAULT_OPTIONS, 
    ...options,
  };

  let finalTranscriptCues = transcriptCues;
  if (transcriptFile) {
    try {
      finalTranscriptCues = await parseTranscriptFile(transcriptFile);
      if (options.overlayText === undefined) {
          finalOptions.overlayText = '';
      }
    } catch (error) {
      console.error('Failed to parse transcript file:', error);
      throw new Error('The provided transcript file could not be parsed.');
    }
  }

  const canvasElement = document.createElement('canvas');
  canvasElement.width = CANVAS_WIDTH;
  canvasElement.height = CANVAS_HEIGHT;

  try {
    const videoBlob = await generateVideo({
      audioFile,
      backgroundImageFile,
      options: finalOptions,
      transcriptCues: finalTranscriptCues,
      canvasElement,
      onProgress,
    });
    return videoBlob;
  } catch (error) {
    console.error('Error during audiogram generation:', error);
    throw error;
  }
}
