import type { TranscriptCue } from '../types';

// Parses timestamp strings like "00:01:02,123" or "00:01:02.123" into seconds.
const parseTimestamp = (timestamp: string): number => {
  const parts = timestamp.split(':');
  const secondsAndMillis = parts.pop()!.split(/[,.]/);
  
  const hours = parts.length > 1 ? parseInt(parts.shift()!, 10) : 0;
  const minutes = parseInt(parts.shift() || '0', 10);
  const seconds = parseInt(secondsAndMillis[0], 10);
  const milliseconds = parseInt(secondsAndMillis[1], 10);

  return (hours * 3600) + (minutes * 60) + seconds + (milliseconds / 1000);
};

export const parseTranscriptCues = (content: string): TranscriptCue[] => {
    if (!content) {
      throw new Error("Transcript content is empty.");
    }
    
    try {
      const cues: TranscriptCue[] = [];
      const cleanedContent = content.replace(/^WEBVTT\s*\n/,'');
      const cueBlocks = cleanedContent.trim().split(/\n\s*\n/);

      for (const block of cueBlocks) {
        const lines = block.split('\n');
        if (lines.length < 2) continue;

        const timeLineIndex = lines.findIndex(line => line.includes('-->'));
        if (timeLineIndex === -1) continue;
        
        const timeLine = lines[timeLineIndex];
        const textLines = lines.slice(timeLineIndex + 1);
        const timeMatch = timeLine.match(/(\S+)\s*-->\s*(\S+)/);

        if (timeMatch) {
          const startTime = parseTimestamp(timeMatch[1]);
          const endTime = parseTimestamp(timeMatch[2]);
          const text = textLines.join(' ').replace(/<[^>]+>/g, '').trim();
          
          if (!isNaN(startTime) && !isNaN(endTime) && text) {
            cues.push({ startTime, endTime, text });
          }
        }
      }
      return cues;
    } catch (error) {
      throw new Error("Error parsing transcript content.");
    }
};

export const parseTranscriptFile = (file: File): Promise<TranscriptCue[]> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      try {
        resolve(parseTranscriptCues(content));
      } catch (error) {
        reject(error);
      }
    };
    reader.onerror = () => reject(new Error("Failed to read the file."));
    reader.readAsText(file);
  });
};
