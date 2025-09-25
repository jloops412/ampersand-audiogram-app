
let audioContext: AudioContext;

function getAudioContext(): AudioContext {
  if (!audioContext) {
    audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
  }
  return audioContext;
}

export async function processAudioFile(file: File): Promise<AudioBuffer> {
  const context = getAudioContext();
  const arrayBuffer = await file.arrayBuffer();
  // Using decodeAudioData with a promise
  return new Promise((resolve, reject) => {
    context.decodeAudioData(
      arrayBuffer,
      (buffer) => resolve(buffer),
      (error) => reject(new Error(`Error decoding audio data: ${error.message}`))
    );
  });
}

export function getStaticPeaks(audioBuffer: AudioBuffer, targetPoints: number): number[] {
    const channelData = audioBuffer.getChannelData(0);
    const sampleSize = Math.floor(channelData.length / targetPoints);
    const peaks: number[] = [];
    for (let i = 0; i < targetPoints; i++) {
        const start = i * sampleSize;
        const end = start + sampleSize;
        let max = 0;
        for (let j = start; j < end; j++) {
            const sample = Math.abs(channelData[j]);
            if (sample > max) {
                max = sample;
            }
        }
        peaks.push(max);
    }
    return peaks;
}