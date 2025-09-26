
import React, { useState, useEffect } from 'react';
import { ControlPanel } from './components/ControlPanel';
import { Preview } from './components/Preview';
import { LoaderIcon } from './components/icons';
import { createAudiogram } from './services/api';
import { processAudioFile } from './services/audioService';
import { parseTranscriptFile } from './services/transcriptService';
import type { CustomizationOptions, TranscriptCue } from './types';
import { DEFAULT_OPTIONS } from './constants';

function App() {
  const [options, setOptions] = useState<CustomizationOptions>(DEFAULT_OPTIONS);
  
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [backgroundImageFile, setBackgroundImageFile] = useState<File | null>(null);
  const [transcriptFile, setTranscriptFile] = useState<File | null>(null);

  const [audioBuffer, setAudioBuffer] = useState<AudioBuffer | null>(null);
  const [backgroundImageUrl, setBackgroundImageUrl] = useState<string | null>(null);
  const [transcriptCues, setTranscriptCues] = useState<TranscriptCue[] | null>(null);

  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!audioFile) {
      setAudioBuffer(null);
      return;
    }
    processAudioFile(audioFile)
      .then(setAudioBuffer)
      .catch(err => {
        console.error('Error processing audio:', err);
        setError('Failed to process audio file.');
      });
  }, [audioFile]);

  useEffect(() => {
    if (!backgroundImageFile) {
      setBackgroundImageUrl(null);
      return;
    }
    const url = URL.createObjectURL(backgroundImageFile);
    setBackgroundImageUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [backgroundImageFile]);
  
  useEffect(() => {
    if (!transcriptFile) {
      setTranscriptCues(null);
      // Restore overlay text if transcript is removed
      if (options.overlayText === '') {
        setOptions(prev => ({...prev, overlayText: DEFAULT_OPTIONS.overlayText}));
      }
      return;
    }
    parseTranscriptFile(transcriptFile)
      .then(cues => {
        setTranscriptCues(cues);
        // Clear overlay text when transcript is loaded
        setOptions(prev => ({...prev, overlayText: ''}));
      })
      .catch(err => {
        console.error('Error parsing transcript:', err);
        setError('Failed to parse transcript file.');
        setTranscriptFile(null); // Reset file state on error
      });
  }, [transcriptFile]);

  const handleGenerateVideo = async () => {
    if (!audioFile) {
      setError('An audio file is required.');
      return;
    }

    setIsGenerating(true);
    setProgress(0);
    setError(null);
    setVideoUrl(null);

    try {
      const videoBlob = await createAudiogram({
        audioFile,
        backgroundImageFile,
        transcriptFile,
        options,
        onProgress: setProgress,
      });
      const url = URL.createObjectURL(videoBlob);
      setVideoUrl(url);
    } catch (err) {
      console.error('Video generation failed:', err);
      setError(err instanceof Error ? err.message : 'An unknown error occurred during video generation.');
    } finally {
      setIsGenerating(false);
      setProgress(100);
    }
  };

  return (
    <div className="bg-gray-800 text-white min-h-screen font-sans">
      <style>{`
        /* Minimalist scrollbar styling */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #2d3748; }
        ::-webkit-scrollbar-thumb { background: #4a5568; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #718096; }
        .bg-primary { background-color: #4A90E2; }
        .bg-primary-dark { background-color: #357ABD; }
        .text-primary { color: #4A90E2; }
        .border-primary { border-color: #4A90E2; }
      `}</style>
      <header className="bg-gray-900 shadow-md p-4 flex justify-between items-center">
        <h1 className="text-xl font-bold">Audiogram Generator</h1>
      </header>
      
      <main className="flex flex-col md:flex-row" style={{ height: 'calc(100vh - 64px)' }}>
        <div className="md:w-1/3 lg:w-1/4 border-r border-gray-700 h-full overflow-y-auto">
          <ControlPanel
            options={options}
            setOptions={setOptions}
            onAudioFileChange={setAudioFile}
            onBackgroundImageChange={setBackgroundImageFile}
            onTranscriptFileChange={setTranscriptFile}
            audioFileName={audioFile?.name}
            backgroundImageFileName={backgroundImageFile?.name}
            transcriptFileName={transcriptFile?.name}
            onGenerate={handleGenerateVideo}
            isGenerating={isGenerating}
          />
        </div>

        <div className="flex-1 flex flex-col items-center justify-center p-6 bg-black/20">
            {error && (
              <div className="absolute top-20 bg-red-500 text-white p-3 rounded-md shadow-lg z-10">
                <p>{error}</p>
                <button onClick={() => setError(null)} className="absolute top-1 right-2 font-bold">&times;</button>
              </div>
            )}
          <div className="w-full max-w-4xl aspect-video bg-black rounded-lg shadow-2xl overflow-hidden relative">
            {isGenerating && (
              <div className="absolute inset-0 bg-black/70 flex flex-col items-center justify-center z-10">
                <LoaderIcon className="w-16 h-16 animate-spin text-primary"/>
                <p className="mt-4 text-xl">Generating video...</p>
                <div className="w-1/2 mt-4 bg-gray-700 rounded-full h-2.5">
                    <div className="bg-primary h-2.5 rounded-full" style={{ width: `${progress}%` }}></div>
                </div>
                <p className="mt-2 text-sm text-gray-400">{Math.round(progress)}%</p>
              </div>
            )}
            
            {videoUrl ? (
                <video src={videoUrl} controls autoPlay className="w-full h-full object-contain" />
            ) : (
                <Preview 
                    audioBuffer={audioBuffer}
                    backgroundImageUrl={backgroundImageUrl}
                    options={options}
                    transcriptCues={transcriptCues}
                />
            )}
          </div>
           {videoUrl && !isGenerating && (
                <a 
                    href={videoUrl} 
                    download={`audiogram-${Date.now()}.webm`}
                    className="mt-6 bg-primary hover:bg-primary-dark text-white font-bold py-2 px-6 rounded-md transition-colors"
                >
                    Download Video
                </a>
            )}
        </div>
      </main>
    </div>
  );
}

export default App;
