
import { useState, useEffect, useRef } from 'react';
import { ControlPanel } from './components/ControlPanel';
import { Preview } from './components/Preview';
import { processAudioFile } from './services/audioService';
import { parseTranscriptCues, parseTranscriptFile } from './services/transcriptService';
import { createAudiogram } from './services/api';
import { runAuphonicProduction } from './services/auphonicService';
import { DEFAULT_OPTIONS } from './constants';
import type { CustomizationOptions, TranscriptCue } from './types';
import { LoaderIcon } from './components/icons';

function App() {
  const [options, setOptions] = useState<CustomizationOptions>(DEFAULT_OPTIONS);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [backgroundImageFile, setBackgroundImageFile] = useState<File | null>(null);
  const [transcriptFile, setTranscriptFile] = useState<File | null>(null);
  
  const [audioBuffer, setAudioBuffer] = useState<AudioBuffer | null>(null);
  const [backgroundImageUrl, setBackgroundImageUrl] = useState<string | null>(null);
  const [transcriptCues, setTranscriptCues] = useState<TranscriptCue[] | null>(null);
  
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationStatus, setGenerationStatus] = useState('');
  const [progress, setProgress] = useState(0);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const previewCanvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (audioFile) {
      processAudioFile(audioFile).then(setAudioBuffer).catch(err => {
        console.error("Error processing audio:", err);
        setError("Failed to process audio file.");
        setAudioFile(null);
      });
    } else {
      setAudioBuffer(null);
    }
  }, [audioFile]);

  useEffect(() => {
    if (backgroundImageFile) {
      const url = URL.createObjectURL(backgroundImageFile);
      setBackgroundImageUrl(url);
      return () => URL.revokeObjectURL(url);
    } else {
      setBackgroundImageUrl(null);
    }
  }, [backgroundImageFile]);
  
  useEffect(() => {
    if (transcriptFile) {
        parseTranscriptFile(transcriptFile).then(cues => {
            setTranscriptCues(cues);
            // Clear static text when transcript is loaded
            setOptions(prev => ({...prev, overlayText: ''}));
        }).catch(err => {
            console.error("Error parsing transcript:", err);
            setError("Failed to parse transcript file.");
            setTranscriptFile(null);
        });
    } else {
        setTranscriptCues(null);
    }
  }, [transcriptFile]);

  const handleGenerateClick = async () => {
    if (!audioFile) {
      setError("An audio file is required.");
      return;
    }
    setIsGenerating(true);
    setProgress(0);
    setError(null);
    setVideoUrl(null);
    setGenerationStatus('Starting...');

    try {
      let finalAudioFile = audioFile;
      let finalTranscriptFile: File | null = transcriptFile;
      let preloadedCues = transcriptCues;

      if (options.enhanceWithAuphonic) {
        setGenerationStatus('Processing audio with Auphonic...');
        const auphonicResult = await runAuphonicProduction({
          audioFile,
          coverImageFile: backgroundImageFile,
          generateTranscript: options.generateTranscript,
          onProgress: (status) => setGenerationStatus(`Auphonic: ${status}`),
        });

        const audioBlob = await fetch(auphonicResult.audioUrl).then(res => res.blob());
        finalAudioFile = new File([audioBlob], `auphonic_${audioFile.name}`, { type: audioBlob.type });

        if (auphonicResult.transcriptUrl) {
            const transcriptText = await fetch(auphonicResult.transcriptUrl).then(res => res.text());
            const parsedCues = parseTranscriptCues(transcriptText);
            preloadedCues = parsedCues;
            setTranscriptCues(parsedCues);
            // Nullify the original transcript file as we're now using the Auphonic-generated one
            finalTranscriptFile = null; 
            // Also ensure static text is cleared
            setOptions(prev => ({...prev, overlayText: ''}));
        }
      }
      
      setGenerationStatus('Generating video...');
      const videoBlob = await createAudiogram({
        audioFile: finalAudioFile,
        backgroundImageFile,
        // Pass null for transcriptFile if cues are already loaded from Auphonic
        transcriptFile: finalTranscriptFile,
        options,
        // Pass already parsed cues if available from Auphonic
        preloadedTranscriptCues: preloadedCues,
        onProgress: setProgress,
      });

      const url = URL.createObjectURL(videoBlob);
      setVideoUrl(url);
    } catch (err) {
      console.error('Generation failed', err);
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred during video generation.';
      setError(errorMessage);
    } finally {
      setIsGenerating(false);
      setGenerationStatus('');
    }
  };

  return (
    <div className="bg-gray-800 text-white h-screen w-screen flex flex-col font-sans">
      <header className="bg-gray-900 shadow-md p-4 text-center">
        <h1 className="text-2xl font-bold text-primary">Audiogram Studio</h1>
      </header>
      <main className="flex flex-1 overflow-hidden">
        <div className="flex-1 flex flex-col items-center justify-center p-8 bg-black relative">
          {isGenerating && (
            <div className="absolute inset-0 bg-black bg-opacity-75 flex flex-col items-center justify-center z-10">
              <LoaderIcon className="w-16 h-16 animate-spin text-primary mb-4" />
              <p className="text-xl mb-2">{generationStatus}</p>
              {generationStatus === 'Generating video...' && (
                <>
                  <div className="w-1/2 bg-gray-700 rounded-full h-2.5 mt-2">
                    <div className="bg-primary h-2.5 rounded-full" style={{ width: `${progress}%` }}></div>
                  </div>
                  <p className="mt-2 text-sm text-gray-400">{Math.round(progress)}</p>
                </>
              )}
            </div>
          )}
          {error && (
            <div className="absolute top-4 left-4 right-4 bg-red-800 text-white p-4 rounded-md z-20">
              <p><strong>Error:</strong> {error}</p>
              <button onClick={() => setError(null)} className="absolute top-2 right-3 font-bold">X</button>
            </div>
          )}
          {videoUrl ? (
            <div className="w-full max-w-4xl aspect-square">
              <video src={videoUrl} controls className="w-full h-full" />
              <div className="mt-4 text-center">
                <a href={videoUrl} download="audiogram.webm" className="bg-primary hover:bg-primary-dark text-white font-bold py-2 px-4 rounded">
                  Download Video
                </a>
                <button onClick={() => setVideoUrl(null)} className="ml-4 bg-gray-600 hover:bg-gray-500 text-white font-bold py-2 px-4 rounded">
                  Create Another
                </button>
              </div>
            </div>
          ) : (
            <div className="w-full max-w-4xl aspect-square bg-black">
              <Preview
                ref={previewCanvasRef}
                audioBuffer={audioBuffer}
                backgroundImageUrl={backgroundImageUrl}
                options={options}
                transcriptCues={transcriptCues}
              />
            </div>
          )}
        </div>
        <ControlPanel
          options={options}
          setOptions={setOptions}
          onGenerate={handleGenerateClick}
          isGenerating={isGenerating}
          onAudioFileChange={setAudioFile}
          onImageFileChange={setBackgroundImageFile}
          onTranscriptFileChange={setTranscriptFile}
          audioFileName={audioFile?.name}
          imageFileName={backgroundImageFile?.name}
          transcriptFileName={transcriptFile?.name}
        />
      </main>
    </div>
  );
}

export default App;
