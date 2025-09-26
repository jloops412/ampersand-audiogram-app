import { useState, useCallback, useEffect, useRef } from 'react';
import { ControlPanel } from './components/ControlPanel';
import { Preview } from './components/Preview';
import { LoaderIcon } from './components/icons';
import type { CustomizationOptions, TranscriptCue } from './types';
import { DEFAULT_OPTIONS } from './constants';
import { processAudioFile } from './services/audioService';
import { generateVideo } from './services/videoService';
import { parseTranscriptFile, parseTranscriptCues } from './services/transcriptService';
import { runProduction as runAuphonicProduction } from './services/auphonicService';

export default function App() {
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [audioBuffer, setAudioBuffer] = useState<AudioBuffer | null>(null);
  const [backgroundImageFile, setBackgroundImageFile] = useState<File | null>(null);
  const [backgroundImageUrl, setBackgroundImageUrl] = useState<string | null>(null);
  const [transcriptFile, setTranscriptFile] = useState<File | null>(null);
  const [transcriptCues, setTranscriptCues] = useState<TranscriptCue[] | null>(null);
  
  const [options, setOptions] = useState<CustomizationOptions>(DEFAULT_OPTIONS);
  const [isLoadingAudio, setIsLoadingAudio] = useState<boolean>(false);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [generationProgress, setGenerationProgress] = useState<number>(0);
  const [generatedVideoUrl, setGeneratedVideoUrl] = useState<string | null>(null);

  const [generationStatusMessage, setGenerationStatusMessage] = useState<string>('');
  
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (backgroundImageFile) {
      const url = URL.createObjectURL(backgroundImageFile);
      setBackgroundImageUrl(url);
      return () => URL.revokeObjectURL(url);
    } else {
      setBackgroundImageUrl(null);
    }
  }, [backgroundImageFile]);
  
  const handleAudioFileChange = useCallback(async (file: File | null) => {
    setAudioFile(file);
    if (file) {
      setIsLoadingAudio(true);
      setGeneratedVideoUrl(null);
      try {
        const buffer = await processAudioFile(file);
        setAudioBuffer(buffer);
      } catch (error) {
        console.error("Error processing audio file:", error);
        alert("Failed to process audio file. Please try a different file.");
        setAudioFile(null);
        setAudioBuffer(null);
      } finally {
        setIsLoadingAudio(false);
      }
    } else {
      setAudioBuffer(null);
    }
  }, []);

  const handleBackgroundImageChange = useCallback((file: File | null) => {
    setBackgroundImageFile(file);
    setGeneratedVideoUrl(null);
  }, []);

  const handleTranscriptFileChange = useCallback(async (file: File | null) => {
    setTranscriptFile(file);
    setTranscriptCues(null);
    if (file) {
      setOptions(prev => ({ ...prev, enhanceWithAuphonic: false, generateTranscript: false, overlayText: '' }));
      try {
        const cues = await parseTranscriptFile(file);
        setTranscriptCues(cues);
      } catch (error) {
        console.error("Error parsing transcript file:", error);
        alert("Failed to parse transcript file. Please check the file format (SRT or VTT).");
        setTranscriptFile(null);
      }
    }
  }, []);

  const handleOverlayTextChange = (text: string) => {
    setOptions(prev => ({ ...prev, overlayText: text }));
    if (text) {
        setTranscriptFile(null);
        setTranscriptCues(null);
        setOptions(prev => ({ ...prev, enhanceWithAuphonic: false, generateTranscript: false }));
    }
  }
  
  const handleGenerateVideo = useCallback(async () => {
    if (!audioFile || !canvasRef.current) {
      alert("Please upload an audio file first.");
      return;
    }
    if (!window.MediaRecorder) {
      alert("Your browser does not support the MediaRecorder API, which is required for video generation. Please try Chrome or Firefox.");
      return;
    }

    setIsGenerating(true);
    setGenerationProgress(0);
    setGeneratedVideoUrl(null);

    try {
      let finalAudioFile = audioFile;
      let finalTranscriptCues = transcriptCues;
      
      if (options.enhanceWithAuphonic) {
        setGenerationStatusMessage('Starting Auphonic production...');
        const auphonicResult = await runAuphonicProduction({
          audioFile,
          coverImageFile: backgroundImageFile,
          generateTranscript: options.generateTranscript,
          onProgress: setGenerationStatusMessage,
        });
        
        finalAudioFile = auphonicResult.enhancedAudioFile;
        // Re-process the enhanced audio file to update the preview waveform
        const newBuffer = await processAudioFile(finalAudioFile);
        setAudioBuffer(newBuffer);

        if (auphonicResult.transcriptText) {
            const cues = parseTranscriptCues(auphonicResult.transcriptText);
            finalTranscriptCues = cues;
            setTranscriptCues(cues);
        }
      }
      
      setGenerationStatusMessage('Rendering video frames...');

      const videoBlob = await generateVideo({
        audioFile: finalAudioFile,
        backgroundImageFile,
        options,
        transcriptCues: finalTranscriptCues,
        canvasElement: canvasRef.current,
        onProgress: setGenerationProgress,
      });
      const videoUrl = URL.createObjectURL(videoBlob);
      setGeneratedVideoUrl(videoUrl);

    } catch (error) {
      console.error("Error generating video:", error);
      alert(`An error occurred during video generation: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setIsGenerating(false);
      setGenerationStatusMessage('');
    }
  }, [audioFile, backgroundImageFile, options, transcriptCues]);

  useEffect(() => {
      if (generatedVideoUrl && videoRef.current) {
          videoRef.current.load();
      }
  }, [generatedVideoUrl]);

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col items-center p-4 sm:p-6 lg:p-8">
      <header className="w-full max-w-7xl text-center mb-8">
        <h1 className="text-4xl sm:text-5xl font-bold text-white tracking-tight">
          Ampersand <span className="text-primary">Audiogram</span>
        </h1>
        <p className="text-gray-400 mt-2 text-lg">
          Audiogram Waveform Generator
        </p>
      </header>
      
      <main className="w-full max-w-7xl flex flex-col lg:flex-row gap-8">
        <aside className="w-full lg:w-1/3 xl:w-1/4">
          <ControlPanel
            options={options}
            setOptions={setOptions}
            onAudioFileChange={handleAudioFileChange}
            onBackgroundImageChange={handleBackgroundImageChange}
            onTranscriptFileChange={handleTranscriptFileChange}
            onOverlayTextChange={handleOverlayTextChange}
            onGenerateVideo={handleGenerateVideo}
            isGenerating={isGenerating || isLoadingAudio}
            audioFileName={audioFile?.name}
            transcriptFileName={transcriptFile?.name}
          />
        </aside>

        <section className="w-full lg:w-2/3 xl:w-3/4 flex flex-col">
          <div className="aspect-video bg-gray-900 rounded-xl overflow-hidden shadow-2xl shadow-primary/10 border-2 border-gray-800 flex items-center justify-center relative">
            {(isLoadingAudio || isGenerating) && (
              <div className="absolute inset-0 bg-gray-950/80 backdrop-blur-sm z-20 flex flex-col items-center justify-center text-center p-4">
                <LoaderIcon className="w-16 h-16 animate-spin text-primary mb-4" />
                <h2 className="text-2xl font-semibold mb-2">
                  {isLoadingAudio ? 'Analyzing Audio...' : (generationStatusMessage || 'Generating Video...')}
                </h2>
                {isGenerating && !generationStatusMessage && (
                    <>
                        <p className="text-gray-400 mb-4">This may take a few moments. Please keep this tab open.</p>
                        <div className="w-full max-w-sm bg-gray-800 rounded-full h-2.5">
                            <div className="bg-primary h-2.5 rounded-full" style={{ width: `${generationProgress.toFixed(0)}%` }}></div>
                        </div>
                        <p className="mt-2 text-lg font-mono">{generationProgress.toFixed(0)}%</p>
                    </>
                )}
                 {isGenerating && generationStatusMessage && (
                    <p className="text-gray-400 mb-4">Please keep this tab open.</p>
                 )}
              </div>
            )}

            {!generatedVideoUrl && (
              <Preview
                ref={canvasRef}
                audioBuffer={audioBuffer}
                backgroundImageUrl={backgroundImageUrl}
                options={options}
                transcriptCues={transcriptCues}
              />
            )}

            {generatedVideoUrl && (
              <div className="w-full h-full flex flex-col items-center justify-center bg-black">
                <video ref={videoRef} controls className="max-w-full max-h-full" src={generatedVideoUrl} />
              </div>
            )}
            
            {!audioBuffer && !isLoadingAudio && (
                <div className="absolute inset-0 flex items-center justify-center z-10 p-4">
                    <p className="text-gray-500 text-xl text-center">Upload an audio file to begin</p>
                </div>
            )}
          </div>

          {generatedVideoUrl && (
            <div className="mt-6 p-4 bg-gray-900 rounded-lg flex items-center justify-between">
                <p className="font-medium">Your video is ready!</p>
                <a
                    href={generatedVideoUrl}
                    download={`audiogram_${audioFile?.name?.split('.')[0] || 'video'}.webm`}
                    className="px-4 py-2 bg-primary text-gray-950 font-bold rounded-md hover:bg-opacity-90 transition-all transform hover:scale-105"
                >
                    Download Video
                </a>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}