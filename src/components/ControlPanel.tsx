
import React from 'react';
import type { CustomizationOptions } from '../types';
import { WaveformStyle } from '../types';
import { FileUpload } from './FileUpload';
import { FONT_FAMILY_OPTIONS } from '../constants';
import { GenerateIcon } from './icons';

interface ControlPanelProps {
  options: CustomizationOptions;
  setOptions: React.Dispatch<React.SetStateAction<CustomizationOptions>>;
  onAudioFileChange: (file: File | null) => void;
  onBackgroundImageChange: (file: File | null) => void;
  onTranscriptFileChange: (file: File | null) => void;
  audioFileName?: string;
  backgroundImageFileName?: string;
  transcriptFileName?: string;
  onGenerate: () => void;
  isGenerating: boolean;
}

const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
    <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-200 border-b border-gray-700 pb-2 mb-4">{title}</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">{children}</div>
    </div>
);

const Option: React.FC<{ label: string; children: React.ReactNode }> = ({ label, children }) => (
    <div>
        <label className="block text-sm font-medium text-gray-400 mb-1">{label}</label>
        {children}
    </div>
);

export const ControlPanel: React.FC<ControlPanelProps> = ({
  options,
  setOptions,
  onAudioFileChange,
  onBackgroundImageChange,
  onTranscriptFileChange,
  audioFileName,
  backgroundImageFileName,
  transcriptFileName,
  onGenerate,
  isGenerating,
}) => {
    
  const handleOptionChange = <K extends keyof CustomizationOptions>(
    key: K,
    value: CustomizationOptions[K]
  ) => {
    setOptions(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="bg-gray-900 p-6 overflow-y-auto h-full text-white">
      <h2 className="text-2xl font-bold mb-6">Audiogram Controls</h2>

      <Section title="Source Files">
        <FileUpload
            id="audio-file"
            label="Audio File"
            accept="audio/*"
            onFileChange={onAudioFileChange}
            fileName={audioFileName}
            disabled={isGenerating}
            className="md:col-span-2"
        />
        <FileUpload
            id="background-image"
            label="Background Image (optional)"
            accept="image/*"
            onFileChange={onBackgroundImageChange}
            fileName={backgroundImageFileName}
            disabled={isGenerating}
        />
        <FileUpload
            id="transcript-file"
            label="Transcript File (optional .vtt/.srt)"
            accept=".vtt,.srt"
            onFileChange={onTranscriptFileChange}
            fileName={transcriptFileName}
            disabled={isGenerating}
        />
      </Section>

      <Section title="Background">
        <Option label="Background Color">
          <input
            type="color"
            value={options.backgroundColor}
            onChange={e => handleOptionChange('backgroundColor', e.target.value)}
            className="w-full h-10 p-1 bg-gray-800 border border-gray-700 rounded-md"
            disabled={isGenerating}
          />
        </Option>
      </Section>
      
      <Section title="Waveform">
        <Option label="Style">
          <select 
            value={options.waveformStyle}
            onChange={e => handleOptionChange('waveformStyle', e.target.value as WaveformStyle)}
            className="w-full p-2 bg-gray-800 border border-gray-700 rounded-md"
            disabled={isGenerating}
          >
            {Object.values(WaveformStyle).map(style => (
              <option key={style} value={style}>{style}</option>
            ))}
          </select>
        </Option>
        <Option label="Color">
          <input
            type="color"
            value={options.waveformColor}
            onChange={e => handleOptionChange('waveformColor', e.target.value)}
            className="w-full h-10 p-1 bg-gray-800 border border-gray-700 rounded-md"
            disabled={isGenerating}
          />
        </Option>
        <Option label="Opacity">
           <input
            type="range"
            min="0" max="1" step="0.05"
            value={options.waveformOpacity}
            onChange={e => handleOptionChange('waveformOpacity', parseFloat(e.target.value))}
            className="w-full"
            disabled={isGenerating}
          />
        </Option>
         <Option label="Amplitude">
           <input
            type="range"
            min="1" max="500" step="1"
            value={options.amplitude}
            onChange={e => handleOptionChange('amplitude', parseInt(e.target.value, 10))}
            className="w-full"
            disabled={isGenerating}
          />
        </Option>
        <Option label="Position">
            <select
                value={options.waveformPosition}
                onChange={e => handleOptionChange('waveformPosition', e.target.value as 'top'|'middle'|'bottom')}
                className="w-full p-2 bg-gray-800 border border-gray-700 rounded-md"
                disabled={isGenerating}
            >
                <option value="top">Top</option>
                <option value="middle">Middle</option>
                <option value="bottom">Bottom</option>
            </select>
        </Option>
      </Section>

      <Section title="Text Overlay">
        <div className="md:col-span-2">
            <Option label="Text Content">
                <textarea
                    value={options.overlayText}
                    onChange={e => handleOptionChange('overlayText', e.target.value)}
                    rows={3}
                    className="w-full p-2 bg-gray-800 border border-gray-700 rounded-md"
                    placeholder="Enter text to display"
                    disabled={isGenerating || !!transcriptFileName}
                />
                 {transcriptFileName && <p className="text-xs text-gray-500 mt-1">Text content is controlled by the transcript file.</p>}
            </Option>
        </div>
         <Option label="Font Color">
          <input
            type="color"
            value={options.fontColor}
            onChange={e => handleOptionChange('fontColor', e.target.value)}
            className="w-full h-10 p-1 bg-gray-800 border border-gray-700 rounded-md"
            disabled={isGenerating}
          />
        </Option>
        <Option label="Font Size">
           <input
            type="range"
            min="12" max="150" step="1"
            value={options.fontSize}
            onChange={e => handleOptionChange('fontSize', parseInt(e.target.value, 10))}
            className="w-full"
            disabled={isGenerating}
          />
        </Option>
        <Option label="Font Family">
             <select
                value={options.fontFamily}
                onChange={e => handleOptionChange('fontFamily', e.target.value)}
                className="w-full p-2 bg-gray-800 border border-gray-700 rounded-md"
                disabled={isGenerating}
            >
                {FONT_FAMILY_OPTIONS.map(font => (
                    <option key={font} value={font}>{font}</option>
                ))}
            </select>
        </Option>
        <Option label="Text Align">
             <select
                value={options.textAlign}
                onChange={e => handleOptionChange('textAlign', e.target.value as 'left'|'center'|'right')}
                className="w-full p-2 bg-gray-800 border border-gray-700 rounded-md"
                disabled={isGenerating}
            >
                <option value="left">Left</option>
                <option value="center">Center</option>
                <option value="right">Right</option>
            </select>
        </Option>
        <Option label="Text Position">
             <select
                value={options.textPosition}
                onChange={e => handleOptionChange('textPosition', e.target.value as 'top'|'middle'|'bottom')}
                className="w-full p-2 bg-gray-800 border border-gray-700 rounded-md"
                disabled={isGenerating}
            >
                <option value="top">Top</option>
                <option value="middle">Middle</option>
                <option value="bottom">Bottom</option>
            </select>
        </Option>
      </Section>

      <div className="mt-8 sticky bottom-0 bg-gray-900 py-4">
        <button
          onClick={onGenerate}
          disabled={isGenerating || !audioFileName}
          className="w-full flex items-center justify-center bg-primary hover:bg-primary-dark disabled:bg-gray-600 text-white font-bold py-3 px-4 rounded-md transition-colors"
        >
          <GenerateIcon className="w-5 h-5 mr-2"/>
          {isGenerating ? 'Generating...' : 'Generate Video'}
        </button>
      </div>
    </div>
  );
};
