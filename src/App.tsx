
import React, { useState, useEffect, useRef } from 'react';
import { ControlPanel } from './components/ControlPanel';
import { Preview } from './components/Preview';
import { createAudiogram } from './services/api';
import { processAudioFile } from './services/audioService';
import { parseTranscriptFile } from './services/transcriptService';
import { getAuphonicPresets } from './services/auphonicService';
import type { CustomizationOptions, TranscriptCue, AuphonicPreset } from './types';
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
  const [generationProgress, setGenerationProgress] = useState(0);
  const [generatedVideoUrl, setGeneratedVideoUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [auphonicToken, setAuphonicToken] = useState<string>('');
  const [auphonicPresets, setAuphonicPresets] = useState<AuphonicPreset[] | null>(null);
  const [isAuphonicLoading, setIsAuphonicLoading] = useState<boolean>(false);
  const auphonicTokenRef = useRef(auphonicToken);
  auphonicTokenRef.current = auphonicToken;
  
  const previewCanvasRef = useRef<HTMLCanvasElement>(null);

  // Effect for handling audio file changes
  useEffect(() => {
    if (!audioFile) {
      setAudioBuffer(null);
      return;
    }
    let active = true;
    processAudioFile(audioFile).then(buffer => {
      if (active) setAudioBuffer(buffer);
    }).catch(err => {
        console.error("Error processing audio file:", err);
        setError("Could not process the audio file. It might be corrupted or in an unsupported format.");
    });
    return () => { active = false; };
  }, [audioFile]);

  // Effect for handling background image changes
  useEffect(() => {
    if (!backgroundImageFile) {
      setBackgroundImageUrl(null);
      return;
    }
    const url = URL.createObjectURL(backgroundImageFile);
    setBackgroundImageUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [backgroundImageFile]);

  // Effect for handling transcript file changes
  useEffect(() => {
    if (!transcriptFile) {
      setTranscriptCues(null);
      // If transcript is removed, restore overlay text if it was cleared
      if (options.overlayText === '') {
        setOptions(opts => ({...opts, overlayText: DEFAULT_OPTIONS.overlayText}));
      }
      return;
    }
    parseTranscriptFile(transcriptFile).then(cues => {
        setTranscriptCues(cues);
        // If a transcript is added, clear the static overlay text
        setOptions(opts => ({...opts, overlayText: ''}));
    }).catch(err => {
        console.error("Error parsing transcript file:", err);
        setError("Could not parse the transcript file. Please check its format.");
    });
  }, [transcriptFile]);

  // Effect to fetch Auphonic presets when token changes
  useEffect(() => {
    const token = auphonicTokenRef.current;
    if (token) {
      setIsAuphonicLoading(true);
      getAuphonicPresets(token)
        .then(setAuphonicPresets)
        .catch(err => {
          console.error(err);
          setError(`Auphonic Error: ${err.message}`);
          setAuphonicPresets(null);
        })
        .finally(() => setIsAuphonicLoading(false));
    } else {
      setAuphonicPresets(null);
    }
  }, [auphonicToken]);

  const handleGenerateClick = async () => {
    if (!audioFile) {
      setError('An audio file is required to generate a video.');
      return;
    }

    setIsGenerating(true);
    setGeneratedVideoUrl(null);
    setError(null);
    setGenerationProgress(0);

    try {
      const videoBlob = await createAudiogram({
        audioFile,
        backgroundImageFile,
        transcriptFile,
        options,
        onProgress: setGenerationProgress,
      });
      const url = URL.createObjectURL(videoBlob);
      setGeneratedVideoUrl(url);
    } catch (err: any) {
      console.error('Generation failed:', err);
      setError(`Failed to generate video: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };
  
  const handleAuphonicSubmit = async () => {
      // TODO: This is a placeholder for a more complete implementation
      alert("Auphonic processing not fully implemented in this demo. Check console for API calls.");
      console.log("Submitting to Auphonic with token and selected preset...");
  }

  return (
    <div className="bg-gray-800 text-white h-screen flex flex-col font-sans">
      <header className="bg-gray-900 shadow-md p-4 z-10">
        <h1 className="text-2xl font-bold text-center">Audiogram Creator</h1>
      </header>
      <main className="flex flex-1 overflow-hidden">
        <ControlPanel
          options={options}
          setOptions={setOptions}
          onAudioFileChange={setAudioFile}
          onBackgroundImageChange={setBackgroundImageFile}
          onTranscriptFileChange={setTranscriptFile}
          onGenerate={handleGenerateClick}
          isGenerating={isGenerating}
          generationProgress={generationProgress}
          audioFileName={audioFile?.name || null}
          backgroundImageName={backgroundImageFile?.name || null}
          transcriptFileName={transcriptFile?.name || null}
          auphonicToken={auphonicToken}
          setAuphonicToken={setAuphonicToken}
          auphonicPresets={auphonicPresets}
          isAuphonicLoading={isAuphonicLoading}
          onAuphonicSubmit={handleAuphonicSubmit}
        />
        <div className="flex-1 flex flex-col items-center justify-center p-8 bg-black">
          {error && <div className="absolute top-20 z-20 bg-red-600 text-white p-4 rounded-md shadow-lg">{error}</div>}
          
          <div className="w-full max-w-4xl aspect-video bg-gray-900 rounded-lg shadow-2xl overflow-hidden relative">
            {generatedVideoUrl ? (
                <video src={generatedVideoUrl} controls autoPlay className="w-full h-full" />
            ) : (
                <Preview
                    ref={previewCanvasRef}
                    audioBuffer={audioBuffer}
                    backgroundImageUrl={backgroundImageUrl}
                    options={options}
                    transcriptCues={transcriptCues}
                />
            )}
            {isGenerating && (
                <div className="absolute inset-0 bg-black bg-opacity-70 flex items-center justify-center">
                    <div className="text-center">
                        <p className="text-2xl mb-4">Generating Video...</p>
                        <div className="w-64 bg-gray-700 rounded-full h-4">
                            <div className="bg-primary h-4 rounded-full" style={{ width: `${generationProgress}%` }}></div>
                        </div>
                         <p className="text-lg mt-2">{generationProgress.toFixed(0)}%</p>
                    </div>
                </div>
            )}
          </div>
          {generatedVideoUrl && (
             <div className="mt-4">
                <a href={generatedVideoUrl} download="audiogram.webm" className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-6 rounded transition-colors">
                    Download Video
                </a>
             </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
