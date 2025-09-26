
import React from 'react';
import type { CustomizationOptions } from '../types';
import { WaveformStyle } from '../types';
import { FileUpload } from './FileUpload';
import { GenerateIcon } from './icons';

interface ControlPanelProps {
  options: CustomizationOptions;
  onOptionsChange: (newOptions: Partial<CustomizationOptions>) => void;
  onAudioFileChange: (file: File | null) => void;
  onBackgroundImageChange: (file: File | null) => void;
  onTranscriptFileChange: (file: File | null) => void;
  onGenerate: () => void;
  isGenerating: boolean;
  audioFileName?: string;
  backgroundImageName?: string;
  transcriptFileName?: string;
}

// A simple reusable input component
const OptionInput: React.FC<{
    label: string;
    type: string;
    value: string | number;
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void;
    min?: number;
    max?: number;
    step?: number;
    className?: string;
    name?: string;
}> = ({ label, ...props }) => (
    <div className={props.className}>
        <label htmlFor={props.name || label} className="block text-sm font-medium text-gray-400 mb-1">{label}</label>
        <input 
            id={props.name || label}
            {...props} 
            className="w-full bg-gray-700 text-white rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
        />
    </div>
);

// A simple reusable select component
const OptionSelect: React.FC<{
    label: string;
    value: string;
    onChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
    children: React.ReactNode;
    className?: string;
    name?: string;
}> = ({ label, ...props }) => (
    <div className={props.className}>
        <label htmlFor={props.name || label} className="block text-sm font-medium text-gray-400 mb-1">{label}</label>
        <select 
            id={props.name || label}
            {...props}
            className="w-full bg-gray-700 text-white rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-primary"
        />
    </div>
);


export const ControlPanel: React.FC<ControlPanelProps> = ({
  options,
  onOptionsChange,
  onAudioFileChange,
  onBackgroundImageChange,
  onTranscriptFileChange,
  onGenerate,
  isGenerating,
  audioFileName,
  backgroundImageName,
  transcriptFileName,
}) => {

  const handleOptionChange = (key: keyof CustomizationOptions, value: any) => {
    onOptionsChange({ [key]: value });
  };
  
  const handleNumericOptionChange = (key: keyof CustomizationOptions, value: string) => {
    onOptionsChange({ [key]: Number(value) });
  }

  return (
    <div className="bg-gray-900 text-white p-6 overflow-y-auto h-full flex flex-col">
      <h2 className="text-xl font-bold mb-6 text-center">Audiogram Generator</h2>
      
      {/* File Uploads */}
      <div className="space-y-4 mb-6 border-b border-gray-700 pb-6">
          <FileUpload
              id="audio-upload"
              label="Audio File"
              accept="audio/*"
              onFileChange={onAudioFileChange}
              disabled={isGenerating}
              fileName={audioFileName}
          />
          <FileUpload
              id="bg-image-upload"
              label="Background Image (Optional)"
              accept="image/*"
              onFileChange={onBackgroundImageChange}
              disabled={isGenerating}
              fileName={backgroundImageName}
          />
           <FileUpload
              id="transcript-upload"
              label="Transcript File (Optional .vtt, .srt)"
              accept=".vtt,.srt"
              onFileChange={onTranscriptFileChange}
              disabled={isGenerating}
              fileName={transcriptFileName}
          />
      </div>

      <div className="flex-grow overflow-y-auto pr-2 -mr-2">
        <div className="space-y-4">
            {/* Waveform Options */}
            <h3 className="font-semibold text-lg border-b border-gray-700 pb-1 mb-2">Waveform</h3>
            <OptionSelect name="waveform-style" label="Style" value={options.waveformStyle} onChange={e => handleOptionChange('waveformStyle', e.target.value)}>
                {Object.values(WaveformStyle).map(style => <option key={style} value={style}>{style.charAt(0).toUpperCase() + style.slice(1).replace('-', ' ')}</option>)}
            </OptionSelect>
             <OptionSelect name="waveform-position" label="Position" value={options.waveformPosition} onChange={e => handleOptionChange('waveformPosition', e.target.value)}>
                <option value="top">Top</option>
                <option value="middle">Middle</option>
                <option value="bottom">Bottom</option>
            </OptionSelect>
            <div className="grid grid-cols-2 gap-4">
                <OptionInput name="waveform-color" label="Color" type="color" value={options.waveformColor} onChange={e => handleOptionChange('waveformColor', e.target.value)} />
                <OptionInput name="waveform-opacity" label="Opacity" type="range" min={0} max={1} step={0.05} value={options.waveformOpacity} onChange={e => handleNumericOptionChange('waveformOpacity', e.target.value)} />
            </div>
            <OptionInput name="amplitude" label="Amplitude" type="range" min={10} max={500} value={options.amplitude} onChange={e => handleNumericOptionChange('amplitude', e.target.value)} />

            {/* Text Options */}
            <h3 className="font-semibold text-lg border-b border-gray-700 pb-1 my-2">Text & Overlay</h3>
             <OptionInput name="overlay-text" label="Overlay Text" type="text" value={options.overlayText} onChange={e => handleOptionChange('overlayText', e.target.value)} disabled={!!transcriptFileName} />
             <OptionInput name="font-family" label="Font Family" type="text" value={options.fontFamily} onChange={e => handleOptionChange('fontFamily', e.target.value)} />
             <div className="grid grid-cols-2 gap-4">
                 <OptionInput name="font-size" label="Font Size" type="number" value={options.fontSize} onChange={e => handleNumericOptionChange('fontSize', e.target.value)} />
                 <OptionInput name="font-color" label="Font Color" type="color" value={options.fontColor} onChange={e => handleOptionChange('fontColor', e.target.value)} />
             </div>
             <div className="grid grid-cols-2 gap-4">
                <OptionSelect name="text-align" label="Text Align" value={options.textAlign} onChange={e => handleOptionChange('textAlign', e.target.value)}>
                    <option value="left">Left</option>
                    <option value="center">Center</option>
                    <option value="right">Right</option>
                </OptionSelect>
                <OptionSelect name="text-position" label="Text Position" value={options.textPosition} onChange={e => handleOptionChange('textPosition', e.target.value)}>
                    <option value="top">Top</option>
                    <option value="middle">Middle</option>
                    <option value="bottom">Bottom</option>
                </OptionSelect>
             </div>
             
             {/* Background Options */}
             <h3 className="font-semibold text-lg border-b border-gray-700 pb-1 my-2">Background</h3>
             <OptionInput name="bg-color" label="Background Color" type="color" value={options.backgroundColor} onChange={e => handleOptionChange('backgroundColor', e.target.value)} />
        </div>
      </div>


      {/* Generate Button */}
      <div className="mt-6 pt-6 border-t border-gray-700">
        <button
          onClick={onGenerate}
          disabled={isGenerating || !audioFileName}
          className="w-full bg-primary text-white font-bold py-3 px-4 rounded-md hover:bg-primary-dark transition-colors flex items-center justify-center disabled:bg-gray-600 disabled:cursor-not-allowed"
        >
          {isGenerating ? (
            <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Generating...
            </>
          ) : (
            <>
              <GenerateIcon className="w-5 h-5 mr-2" />
              Generate Video
            </>
          )}
        </button>
      </div>
    </div>
  );
};
