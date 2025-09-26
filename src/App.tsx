
import React, { useState, useEffect, useRef } from 'react';
import { ControlPanel } from './components/ControlPanel';
import { Preview } from './components/Preview';
import { createAudiogram } from './services/api';
import { processAudioFile } from './services/audioService';
import { parseTranscriptFile } from './services/transcriptService';
import { DEFAULT_OPTIONS } from './constants';
import type { CustomizationOptions, TranscriptCue } from './types';

const App: React.FC = () => {
  const [options, setOptions] = useState<CustomizationOptions>(DEFAULT_OPTIONS);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [backgroundImageFile, setBackgroundImageFile] = useState<File | null>(null);
  const [transcriptFile, setTranscriptFile] = useState<File | null>(null);
  
  const [audioBuffer, setAudioBuffer] = useState<AudioBuffer | null>(null);
  const [backgroundImageUrl, setBackgroundImageUrl] = useState<string | null>(null);
  const [transcriptCues, setTranscriptCues] = useState<TranscriptCue[] | null>(null);

  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [generatedVideoUrl, setGeneratedVideoUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const previewCanvasRef = useRef<HTMLCanvasElement>(null);

  // Effect to process audio file for preview
  useEffect(() => {
    if (audioFile) {
      processAudioFile(audioFile)
        .then(setAudioBuffer)
        .catch(err => {
            console.error("Error processing audio file:", err);
            setError("Could not process audio file.");
        });
    } else {
      setAudioBuffer(null);
    }
  }, [audioFile]);

  // Effect to create object URL for background image preview
  useEffect(() => {
    if (backgroundImageFile) {
      const url = URL.createObjectURL(backgroundImageFile);
      setBackgroundImageUrl(url);
      return () => URL.revokeObjectURL(url);
    } else {
      setBackgroundImageUrl(null);
    }
  }, [backgroundImageFile]);

   // Effect to parse transcript file for preview
  useEffect(() => {
    if (transcriptFile) {
      parseTranscriptFile(transcriptFile)
        .then(cues => {
          setTranscriptCues(cues);
          // If a transcript is provided, clear the static overlay text for a better preview
          // We only do this if the user hasn't explicitly set it
          if (options.overlayText === DEFAULT_OPTIONS.overlayText) {
             setOptions(prev => ({...prev, overlayText: ''}));
          }
        })
        .catch(err => {
          console.error("Error parsing transcript file:", err);
          setError("Could not parse transcript file.");
        });
    } else {
      setTranscriptCues(null);
    }
  }, [transcriptFile, options.overlayText]);


  const handleOptionsChange = (newOptions: Partial<CustomizationOptions>) => {
    setOptions(prev => ({ ...prev, ...newOptions }));
  };

  const handleGenerate = async () => {
    if (!audioFile) {
      setError('Please select an audio file first.');
      return;
    }
    
    setIsGenerating(true);
    setProgress(0);
    setError(null);
    if(generatedVideoUrl) {
        URL.revokeObjectURL(generatedVideoUrl);
        setGeneratedVideoUrl(null);
    }

    try {
      const videoBlob = await createAudiogram({
        audioFile,
        backgroundImageFile,
        transcriptFile,
        options,
        onProgress: setProgress,
      });
      const url = URL.createObjectURL(videoBlob);
      setGeneratedVideoUrl(url);
    } catch (err) {
      console.error('Generation failed:', err);
      setError(err instanceof Error ? err.message : 'An unknown error occurred during video generation.');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="bg-gray-800 text-white h-screen flex flex-col font-sans">
      <header className="bg-gray-900 shadow-md p-4 text-center">
          <h1 className="text-2xl font-bold tracking-tight">Audiogram Studio</h1>
      </header>
      <div className="flex flex-1 overflow-hidden">
        <aside className="w-96 bg-gray-900 flex-shrink-0">
          <ControlPanel
            options={options}
            onOptionsChange={handleOptionsChange}
            onAudioFileChange={setAudioFile}
            onBackgroundImageChange={setBackgroundImageFile}
            onTranscriptFileChange={setTranscriptFile}
            onGenerate={handleGenerate}
            isGenerating={isGenerating}
            audioFileName={audioFile?.name}
            backgroundImageName={backgroundImageFile?.name}
            transcriptFileName={transcriptFile?.name}
          />
        </aside>
        <main className="flex-1 p-8 flex flex-col items-center justify-center bg-black/50">
           {error && <div className="absolute top-20 bg-red-500 text-white p-4 rounded-md shadow-lg z-10">{error}</div>}
           <div className="w-full max-w-3xl aspect-square flex flex-col items-center justify-center">
            {generatedVideoUrl ? (
                <video src={generatedVideoUrl} controls autoPlay loop className="w-full h-full rounded-lg shadow-2xl" />
            ) : isGenerating ? (
                <div className="w-full h-full flex flex-col items-center justify-center bg-gray-900 rounded-lg shadow-2xl">
                    <div className="w-3/4 bg-gray-700 rounded-full h-4">
                        <div className="bg-primary h-4 rounded-full" style={{ width: `${progress}%` }}></div>
                    </div>
                    <p className="mt-4 text-lg">Generating video... {progress.toFixed(0)}%</p>
                </div>
            ) : (
                <Preview
                    ref={previewCanvasRef}
                    audioBuffer={audioBuffer}
                    backgroundImageUrl={backgroundImageUrl}
                    options={options}
                    transcriptCues={transcriptCues}
                />
            )}
           </div>
           {generatedVideoUrl && (
             <a 
                href={generatedVideoUrl} 
                download="audiogram.webm"
                className="mt-6 bg-primary text-white font-bold py-3 px-6 rounded-md hover:bg-primary-dark transition-colors"
             >
                Download Video
            </a>
           )}
        </main>
      </div>
    </div>
  );
};

export default App;
