# Ampersand Audiogram API Documentation

## Overview

Welcome to the Ampersand Audiogram API! This document provides developers with the information needed to programmatically generate custom audiogram videos using the `createAudiogram` function.

This API is designed to run entirely in the browser. It encapsulates all the complex logic of audio processing, canvas animation, and video encoding into a single, easy-to-use function.

## Getting Started

To use the API, you'll first need to import the `createAudiogram` function from the `services/api.ts` file.

```javascript
import { createAudiogram } from './services/api';
```

The function is asynchronous and returns a `Promise` that resolves with a `Blob` containing the generated video in WebM format.

## API Reference

### `createAudiogram(params)`

This is the sole function exposed by the API. It takes a single object with the following parameters:

| Parameter             | Type                                    | Required | Description                                                                                              |
| --------------------- | --------------------------------------- | -------- | -------------------------------------------------------------------------------------------------------- |
| `audioFile`           | `File`                                  | Yes      | The primary audio file for the audiogram.                                                                |
| `backgroundImageFile` | `File`                                  | No       | An optional background image file (e.g., JPEG, PNG).                                                     |
| `transcriptFile`      | `File`                                  | No       | An optional transcript file in `.srt` or `.vtt` format for synchronized captions.                        |
| `options`             | `Partial<CustomizationOptions>`         | No       | An object with customization options to override the defaults. See the full list below.                  |
| `onProgress`          | `(progress: number) => void`            | No       | An optional callback function that receives the generation progress as a percentage from 0 to 100.         |

**Returns:** `Promise<Blob>` - A promise that resolves with the final video file as a Blob.

---

### `CustomizationOptions` Object

The `options` parameter allows you to control every visual aspect of the audiogram. You only need to provide the properties you want to override from the default settings.

#### General & Color

| Property            | Type     | Default       | Description                                  |
| ------------------- | -------- | ------------- | -------------------------------------------- |
| `waveformStyle`     | `string` | `'Line'`      | The style of the waveform. See `WaveformStyle` enum below. |
| `backgroundColor`   | `string` | `'#1a1b20'`   | The background color in hex format.          |
| `waveformColor`     | `string` | `'#D7B185'`   | The waveform color in hex format.            |
| `waveformOpacity`   | `number` | `1.0`         | A value from `0.0` (transparent) to `1.0` (opaque). |
| `waveformPosition`  | `string` | `'middle'`    | Vertical position. See `TextPosition` enum. (Applies to `Line`, `Mirrored Line`, `Bars`, `Bricks`). |
| `amplitude`         | `number` | `150`         | The overall height/sensitivity of the waveform. |

#### Studio Sound Processing (Audio Enhancement)

These options are contained within an `audioEnhancement` object in the main `options` parameter. They are designed to be used together to produce a professional, clean sound.
Example: `options: { audioEnhancement: { adaptiveNoiseReduction: true, loudnessNormalization: true } }`

| Property                  | Type      | Default | Description                                                                                                |
| ------------------------- | --------- | ------- | ---------------------------------------------------------------------------------------------------------- |
| `adaptiveNoiseReduction`  | `boolean` | `false` | Applies a multi-band noise gate to intelligently reduce background noise and hiss while preserving vocal clarity. |
| `humReduction`            | `boolean` | `false` | Uses notch filters to surgically remove common electrical hum (60Hz and its harmonics).                    |
| `speechClarityEQ`         | `boolean` | `false` | Applies an equalizer to boost frequencies associated with vocal presence and intelligibility.                 |
| `dynamicRangeCompression` | `boolean` | `false` | Acts as a leveler, reducing the volume difference between loud and quiet parts for a consistent, professional sound. |
| `loudnessNormalization`   | `boolean` | `false` | Adjusts the final output to a standard perceived loudness (based on RMS), ideal for consistent playback.   |


#### Line, Circle & Radial Styles

| Property      | Type     | Default   | Description                                              |
| ------------- | -------- | --------- | -------------------------------------------------------- |
| `lineWidth`   | `number` | `3`       | The thickness of the lines used in the waveform.         |
| `lineCap`     | `string` | `'round'` | The line cap style. See `LineCap` enum below.            |

#### Bar & Equalizer Styles

| Property     | Type     | Default | Description                                  |
| ------------ | -------- | ------- | -------------------------------------------- |
| `barCount`   | `number` | `128`   | The number of bars to display.               |
| `barWidth`   | `number` | `5`     | The width of each individual bar.            |
| `barSpacing` | `number` | `2`     | The space between each bar.                  |

#### Circle Style

| Property       | Type     | Default | Description                            |
| -------------- | -------- | ------- | -------------------------------------- |
| `circleRadius` | `number` | `150`   | The inner radius of the circle waveform. |

#### Bricks Style

| Property       | Type     | Default | Description                               |
| -------------- | -------- | ------- | ----------------------------------------- |
| `brickCount`   | `number` | `80`    | The number of brick columns.              |
| `brickHeight`  | `number` | `8`     | The height of each individual brick.      |
| `brickSpacing` | `number` | `4`     | The spacing between brick columns/rows.   |

#### Radial Style

| Property      | Type     | Default | Description                                       |
| ------------- | -------- | ------- | ------------------------------------------------- |
| `spokeCount`  | `number` | `180`   | The number of spokes in the radial waveform.      |
| `innerRadius` | `number` | `50`    | The radius of the empty space in the center.      |

#### Particles Style

| Property        | Type     | Default | Description                             |
| --------------- | -------- | ------- | --------------------------------------- |
| `particleCount` | `number` | `200`   | The maximum number of particles on screen. |
| `particleSize`  | `number` | `3`     | The maximum size of each particle.      |
| `particleSpeed` | `number` | `1.5`   | The maximum speed of each particle.     |

#### Text & Transcript

| Property       | Type     | Default          | Description                                           |
| -------------- | -------- | ---------------- | ----------------------------------------------------- |
| `overlayText`  | `string` | `''`             | Static text to display throughout the video.          |
| `fontFamily`   | `string` | `'Montserrat'`   | The font family (must be loaded in the browser).      |
| `fontSize`     | `number` | `80`             | The font size in pixels.                              |
| `fontColor`    | `string` | `'#ffffff'`      | The text color in hex format.                         |
| `textAlign`    | `string` | `'center'`       | Horizontal alignment. See `TextAlign` enum below.     |
| `textPosition` | `string` | `'middle'`       | Vertical position. See `TextPosition` enum below.     |

---

## Type Enums Reference

These are the possible string values for the corresponding `CustomizationOptions` properties.

-   **`WaveformStyle`**: `'Line'`, `'Mirrored Line'`, `'Bars'`, `'Circle'`, `'Equalizer'`, `'Bricks'`, `'Radial'`, `'Particles'`
-   **`LineCap`**: `'butt'`, `'round'`, `'square'`
-   **`TextAlign`**: `'left'`, `'center'`, `'right'`
-   **`TextPosition`**: `'top'`, `'middle'`, `'bottom'`

---

## Usage Examples

### Example 1: Basic Generation

This example creates a simple audiogram with default styling using only an audio file.

```javascript
import { createAudiogram } from './services/api';

const audioInput = document.getElementById('audio-file-input');

audioInput.addEventListener('change', async (event) => {
  const audioFile = event.target.files[0];

  if (audioFile) {
    try {
      console.log('Starting generation...');
      const videoBlob = await createAudiogram({ audioFile });
      console.log('Generation complete!');

      // Create a URL to preview or download the video
      const videoUrl = URL.createObjectURL(videoBlob);
      
      // Set the source of a video element
      const videoPlayer = document.getElementById('video-player');
      videoPlayer.src = videoUrl;

      // Create a download link
      const downloadLink = document.getElementById('download-link');
      downloadLink.href = videoUrl;
      downloadLink.download = 'audiogram.webm';
      downloadLink.style.display = 'block';

    } catch (error) {
      console.error('An error occurred:', error);
      alert('Failed to generate audiogram.');
    }
  }
});
```

### Example 2: Advanced Customization

This example demonstrates how to use a background image, a transcript file, custom styling options, and a progress tracker.

```javascript
import { createAudiogram } from './services/api';
import { WaveformStyle } from './types'; // Assuming types are accessible

const generateButton = document.getElementById('generate-btn');

generateButton.addEventListener('click', async () => {
  // Assume you get these files from file inputs
  const audioFile = document.getElementById('audio-input').files[0];
  const imageFile = document.getElementById('image-input').files[0];
  const transcriptFile = document.getElementById('transcript-input').files[0];
  const progressBar = document.getElementById('progress-bar');

  if (!audioFile) {
    alert('Please select an audio file.');
    return;
  }
  
  const customOptions = {
    waveformStyle: WaveformStyle.MirroredLine,
    waveformColor: '#ff4500',
    backgroundColor: '#111111',
    amplitude: 200,
    lineWidth: 4,
    fontFamily: 'Lato',
    fontSize: 90,
    fontColor: '#ffffff',
    audioEnhancement: {
      adaptiveNoiseReduction: true,
      humReduction: true,
      dynamicRangeCompression: true,
      loudnessNormalization: true,
    }
  };

  const handleProgress = (progress) => {
    console.log(`Progress: ${progress.toFixed(0)}%`);
    progressBar.style.width = `${progress}%`;
  };

  try {
    const videoBlob = await createAudiogram({
      audioFile,
      backgroundImageFile: imageFile,
      transcriptFile: transcriptFile,
      options: customOptions,
      onProgress: handleProgress,
    });

    const videoUrl = URL.createObjectURL(videoBlob);
    // ... then use videoUrl as in the basic example ...

  } catch (error) {
    console.error('An error occurred:', error);
  }
});
```