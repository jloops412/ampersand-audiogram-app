import type { CustomizationOptions, TranscriptCue } from '../types';
import { DEFAULT_OPTIONS, CANVAS_WIDTH, CANVAS_HEIGHT } from '../constants';
import { generateVideo } from './videoService';
import { parseTranscriptFile } from './transcriptService';

/**
 * @typedef {import('../types').CustomizationOptions} CustomizationOptions
 */

/**
 * Parameters for the createAudiogram API function.
 * @typedef {object} CreateAudiogramParams
 * @property {File} audioFile - The primary audio file for the audiogram.
 * @property {File} [backgroundImageFile] - An optional background image file.
 * @property {File} [transcriptFile] - An optional transcript file (.srt or .vtt).
 * @property {Partial<CustomizationOptions>} [options] - A partial object of customization options to override the defaults.
 * @property {(progress: number) => void} [onProgress] - An optional callback function to track generation progress (0-100).
 */
export interface CreateAudiogramParams {
  audioFile: File;
  backgroundImageFile?: File | null;
  transcriptFile?: File | null;
  options?: Partial<CustomizationOptions>;
  onProgress?: (progress: number) => void;
}

/**
 * Programmatically generates an audiogram video.
 * This function provides a headless, developer-friendly API to the core functionality of the application.
 *
 * @param {CreateAudiogramParams} params - The parameters for generating the audiogram.
 * @returns {Promise<Blob>} A promise that resolves with a Blob containing the generated video in WebM format.
 */
export async function createAudiogram({
  audioFile,
  backgroundImageFile = null,
  transcriptFile = null,
  options = {},
  onProgress = () => {},
}: CreateAudiogramParams): Promise<Blob> {
  if (!audioFile) {
    throw new Error('An audio file is required to create an audiogram.');
  }

  // Merge user options with defaults. Auphonic options are omitted as they are not used in this client-side function.
  const finalOptions: CustomizationOptions = { 
    ...DEFAULT_OPTIONS, 
    ...options,
  };

  // Parse transcript if provided
  let transcriptCues: TranscriptCue[] | null = null;
  if (transcriptFile) {
    try {
      transcriptCues = await parseTranscriptFile(transcriptFile);
      // If a transcript is used, ensure static text is cleared unless specified otherwise
      if (options.overlayText === undefined) {
          finalOptions.overlayText = '';
      }
    } catch (error) {
      console.error('Failed to parse transcript file:', error);
      throw new Error('The provided transcript file could not be parsed.');
    }
  }

  // Create a canvas element in memory to render the video
  const canvasElement = document.createElement('canvas');
  canvasElement.width = CANVAS_WIDTH;
  canvasElement.height = CANVAS_HEIGHT;

  try {
    const videoBlob = await generateVideo({
      audioFile,
      backgroundImageFile,
      options: finalOptions,
      transcriptCues,
      canvasElement,
      onProgress,
    });
    return videoBlob;
  } catch (error) {
    console.error('Error during audiogram generation:', error);
    // Re-throw the error to be caught by the consumer
    throw error;
  }
}
