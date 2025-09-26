import React, { ChangeEvent } from 'react';
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

const OptionToggle: React.FC<{ label: string; checked: boolean; onChange: (e: ChangeEvent<HTMLInputElement>) => void; disabled?: boolean }> = ({ label, checked, onChange, disabled }) => (
    <div className="flex items-center justify-between md:col-span-2 bg-gray-800 p-2 rounded-md">
        <label htmlFor={label} className="text-sm font-medium text-gray-300">{label}</label>
        <label className="relative inline-flex items-center cursor-pointer">
            <input
                id={label}
                type="checkbox"
                checked={checked}
                onChange={onChange}
                className="sr-only peer"
                disabled={disabled}
            />
            <div className="w-11 h-6 bg-gray-700 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary peer-disabled:opacity-50"></div>
        </label>
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
            disabled={isGenerating || options.generateTranscript}
        />
      </Section>
      
      <Section title="Audio Enhancement">
         <OptionToggle
            label="Enhance Audio with Auphonic"
            checked={options.enhanceWithAuphonic}
            onChange={e => {
                handleOptionChange('enhanceWithAuphonic', e.target.checked);
                if (!e.target.checked) {
                    handleOptionChange('generateTranscript', false);
                }
            }}
            disabled={isGenerating}
        />
        <OptionToggle
            label="Generate Transcript"
            checked={options.generateTranscript}
            onChange={e => handleOptionChange('generateTranscript', e.target.checked)}
            disabled={isGenerating || !options.enhanceWithAuphonic}
        />
        {options.enhanceWithAuphonic && <p className="text-xs text-gray-500 md:col-span-2 mt-1">Audio will be processed with Auphonic's default preset for leveling, noise reduction, and loudness targeting.</p>}
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
                    disabled={isGenerating || !!transcriptFileName || options.generateTranscript}
                />
                 {(transcriptFileName || options.generateTranscript) && <p className="text-xs text-gray-500 mt-1">Text content is controlled by the transcript.</p>}
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
