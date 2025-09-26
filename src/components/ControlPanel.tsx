
import React, { ChangeEvent } from 'react';
import type { CustomizationOptions } from '../types';
import { WaveformStyle } from '../types';
import { FileUpload } from './FileUpload';
import { GenerateIcon } from './icons';

interface ControlPanelProps {
  options: CustomizationOptions;
  setOptions: React.Dispatch<React.SetStateAction<CustomizationOptions>>;
  onGenerate: () => void;
  isGenerating: boolean;
  onAudioFileChange: (file: File | null) => void;
  onImageFileChange: (file: File | null) => void;
  onTranscriptFileChange: (file: File | null) => void;
  audioFileName: string | undefined;
  imageFileName: string | undefined;
  transcriptFileName: string | undefined;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  options,
  setOptions,
  onGenerate,
  isGenerating,
  onAudioFileChange,
  onImageFileChange,
  onTranscriptFileChange,
  audioFileName,
  imageFileName,
  transcriptFileName,
}) => {

  const handleOptionChange = (key: keyof CustomizationOptions, value: any) => {
    setOptions(prev => ({ ...prev, [key]: value }));
  };

  const handleToggleChange = (key: keyof CustomizationOptions, value: boolean) => {
    setOptions(prev => {
        const newOptions = { ...prev, [key]: value };
        // If Auphonic is turned off, also turn off transcript generation
        if (key === 'enhanceWithAuphonic' && !value) {
            newOptions.generateTranscript = false;
        }
        return newOptions;
    });
  };

  const waveformOptions = Object.values(WaveformStyle);
  
  const renderWaveformSpecificControls = () => {
    switch(options.waveformStyle) {
      case WaveformStyle.Line:
      case WaveformStyle.MirroredLine:
        return (
          <>
            <RangeSlider label="Line Width" value={options.lineWidth} onChange={(v) => handleOptionChange('lineWidth', v)} min={1} max={20} step={1} disabled={isGenerating}/>
          </>
        )
      case WaveformStyle.Bars:
      case WaveformStyle.Equalizer:
        return (
          <>
            <RangeSlider label="Bar Count" value={options.barCount} onChange={(v) => handleOptionChange('barCount', v)} min={10} max={200} step={2} disabled={isGenerating}/>
            <RangeSlider label="Bar Width" value={options.barWidth} onChange={(v) => handleOptionChange('barWidth', v)} min={1} max={50} step={1} disabled={isGenerating}/>
            <RangeSlider label="Bar Spacing" value={options.barSpacing} onChange={(v) => handleOptionChange('barSpacing', v)} min={0} max={20} step={1} disabled={isGenerating}/>
          </>
        )
      case WaveformStyle.Bricks:
        return (
            <>
              <RangeSlider label="Brick Count" value={options.brickCount} onChange={(v) => handleOptionChange('brickCount', v)} min={10} max={100} step={1} disabled={isGenerating}/>
              <RangeSlider label="Brick Height" value={options.brickHeight} onChange={(v) => handleOptionChange('brickHeight', v)} min={1} max={30} step={1} disabled={isGenerating}/>
              <RangeSlider label="Brick Spacing" value={options.brickSpacing} onChange={(v) => handleOptionChange('brickSpacing', v)} min={0} max={10} step={1} disabled={isGenerating}/>
            </>
        )
      case WaveformStyle.Circle:
        return (
          <>
            <RangeSlider label="Circle Radius" value={options.circleRadius} onChange={(v) => handleOptionChange('circleRadius', v)} min={50} max={400} step={10} disabled={isGenerating}/>
            <RangeSlider label="Line Width" value={options.lineWidth} onChange={(v) => handleOptionChange('lineWidth', v)} min={1} max={20} step={1} disabled={isGenerating}/>
          </>
        )
      case WaveformStyle.Radial:
        return (
          <>
            <RangeSlider label="Inner Radius" value={options.innerRadius} onChange={(v) => handleOptionChange('innerRadius', v)} min={10} max={300} step={5} disabled={isGenerating}/>
            <RangeSlider label="Spoke Count" value={options.spokeCount} onChange={(v) => handleOptionChange('spokeCount', v)} min={20} max={360} step={4} disabled={isGenerating}/>
            <RangeSlider label="Line Width" value={options.lineWidth} onChange={(v) => handleOptionChange('lineWidth', v)} min={1} max={20} step={1} disabled={isGenerating}/>
          </>
        )
      case WaveformStyle.Particles:
        return (
          <>
            <RangeSlider label="Particle Count" value={options.particleCount} onChange={(v) => handleOptionChange('particleCount', v)} min={100} max={2000} step={50} disabled={isGenerating}/>
            <RangeSlider label="Particle Size" value={options.particleSize} onChange={(v) => handleOptionChange('particleSize', v)} min={1} max={10} step={1} disabled={isGenerating}/>
            <RangeSlider label="Particle Speed" value={options.particleSpeed} onChange={(v) => handleOptionChange('particleSpeed', v)} min={1} max={10} step={1} disabled={isGenerating}/>
          </>
        )
      default:
        return null;
    }
  }

  return (
    <div className="bg-gray-900 text-white w-96 p-4 overflow-y-auto flex flex-col h-full border-l border-gray-800">
      <h2 className="text-xl font-bold mb-6 text-center">Customize Audiogram</h2>
      
      <div className="space-y-4 mb-6">
        <FileUpload id="audio-upload" label="Audio File" onFileChange={onAudioFileChange} accept="audio/*" disabled={isGenerating} fileName={audioFileName} />
        <FileUpload id="image-upload" label="Background Image (optional)" onFileChange={onImageFileChange} accept="image/*" disabled={isGenerating} fileName={imageFileName} />
        <FileUpload id="transcript-upload" label="Transcript File (optional, .srt/.vtt)" onFileChange={onTranscriptFileChange} accept=".srt,.vtt" disabled={isGenerating} fileName={transcriptFileName} />
      </div>

      <div className="flex-grow overflow-y-auto pr-2 -mr-2 space-y-6">
        <details open className="group">
          <summary className="font-semibold cursor-pointer list-none group-open:mb-2">Audio Enhancement</summary>
          <div className="pl-4 mt-2 space-y-4 border-l-2 border-gray-700">
            <OptionToggle 
                label="Enhance Audio with Auphonic"
                checked={options.enhanceWithAuphonic}
                onChange={(c) => handleToggleChange('enhanceWithAuphonic', c)}
                disabled={isGenerating}
            />
            <OptionToggle 
                label="Generate Transcript"
                checked={options.generateTranscript}
                onChange={(c) => handleToggleChange('generateTranscript', c)}
                disabled={isGenerating || !options.enhanceWithAuphonic}
            />
            {!options.enhanceWithAuphonic && <p className="text-xs text-gray-500 -mt-2">Transcript generation requires Auphonic enhancement.</p>}
          </div>
        </details>

        <details open className="group">
          <summary className="font-semibold cursor-pointer list-none group-open:mb-2">Waveform</summary>
          <div className="pl-4 mt-2 space-y-4 border-l-2 border-gray-700">
            <Select label="Style" value={options.waveformStyle} onChange={(v) => handleOptionChange('waveformStyle', v)} options={waveformOptions} disabled={isGenerating}/>
            <ColorInput label="Color" value={options.waveformColor} onChange={(v) => handleOptionChange('waveformColor', v)} disabled={isGenerating}/>
            <RangeSlider label="Opacity" value={options.waveformOpacity} onChange={(v) => handleOptionChange('waveformOpacity', v)} min={0} max={1} step={0.1} disabled={isGenerating}/>
            <RangeSlider label="Amplitude" value={options.amplitude} onChange={(v) => handleOptionChange('amplitude', v)} min={10} max={500} step={10} disabled={isGenerating}/>
            <Select label="Position" value={options.waveformPosition} onChange={(v) => handleOptionChange('waveformPosition', v)} options={['top', 'middle', 'bottom']} disabled={isGenerating}/>
            {renderWaveformSpecificControls()}
          </div>
        </details>
        
        <details className="group">
          <summary className="font-semibold cursor-pointer list-none group-open:mb-2">Text & Font</summary>
          <div className="pl-4 mt-2 space-y-4 border-l-2 border-gray-700">
             <textarea 
                value={options.overlayText}
                onChange={(e) => handleOptionChange('overlayText', e.target.value)}
                className="w-full bg-gray-800 rounded p-2 text-sm border border-gray-700 focus:ring-primary focus:border-primary disabled:bg-gray-700"
                rows={3}
                placeholder="Enter text to display"
                disabled={isGenerating || !!transcriptFileName}
              />
              {transcriptFileName && <p className="text-xs text-gray-400 -mt-2">Overlay text is disabled when a transcript is used.</p>}
              <TextInput label="Font Family" value={options.fontFamily} onChange={(v) => handleOptionChange('fontFamily', v)} disabled={isGenerating}/>
              <RangeSlider label="Font Size" value={options.fontSize} onChange={(v) => handleOptionChange('fontSize', v)} min={12} max={200} step={2} disabled={isGenerating}/>
              <ColorInput label="Font Color" value={options.fontColor} onChange={(v) => handleOptionChange('fontColor', v)} disabled={isGenerating}/>
              <Select label="Text Align" value={options.textAlign} onChange={(v) => handleOptionChange('textAlign', v)} options={['left', 'center', 'right']} disabled={isGenerating}/>
              <Select label="Text Position" value={options.textPosition} onChange={(v) => handleOptionChange('textPosition', v)} options={['top', 'middle', 'bottom']} disabled={isGenerating}/>
          </div>
        </details>

        <details className="group">
          <summary className="font-semibold cursor-pointer list-none group-open:mb-2">Background</summary>
           <div className="pl-4 mt-2 space-y-4 border-l-2 border-gray-700">
            <ColorInput label="Background Color" value={options.backgroundColor} onChange={(v) => handleOptionChange('backgroundColor', v)} disabled={isGenerating}/>
           </div>
        </details>
      </div>

      <div className="mt-auto pt-6">
        <button 
          onClick={onGenerate} 
          disabled={isGenerating || !audioFileName}
          className="w-full bg-primary hover:bg-primary-dark text-white font-bold py-3 px-4 rounded-lg flex items-center justify-center disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors"
        >
          {isGenerating ? 'Generating...' : <><GenerateIcon className="w-5 h-5 mr-2" /> Generate Video</>}
        </button>
      </div>
    </div>
  );
};

// Helper components
const RangeSlider: React.FC<{label: string, value: number, onChange: (v: number) => void, min: number, max: number, step: number, disabled?: boolean}> = ({label, value, onChange, ...props}) => (
  <div>
    <label className="block text-sm font-medium text-gray-400 flex justify-between">
      <span>{label}</span>
      <span>{value}</span>
    </label>
    <input type="range" value={value} onChange={(e) => onChange(parseFloat(e.target.value))} {...props} className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary" />
  </div>
);

const ColorInput: React.FC<{label: string, value: string, onChange: (v: string) => void, disabled?: boolean}> = ({label, value, onChange, disabled}) => (
  <div>
    <label className="block text-sm font-medium text-gray-400">{label}</label>
    <div className="relative">
      <input type="color" value={value} onChange={(e) => onChange(e.target.value)} className="w-full h-10 p-0 border-none bg-transparent" disabled={disabled}/>
      <div className="absolute inset-0 rounded-md pointer-events-none border border-gray-700" style={{backgroundColor: value}}></div>
    </div>
  </div>
);

const Select: React.FC<{label: string, value: string, onChange: (v: string) => void, options: string[], disabled?: boolean}> = ({label, value, onChange, options, disabled}) => (
  <div>
    <label className="block text-sm font-medium text-gray-400">{label}</label>
    <select value={value} onChange={(e) => onChange(e.target.value)} className="w-full bg-gray-800 rounded p-2 text-sm border border-gray-700 focus:ring-primary focus:border-primary" disabled={disabled}>
      {options.map(o => <option key={o} value={o}>{o}</option>)}
    </select>
  </div>
);

const TextInput: React.FC<{label: string, value: string, onChange: (v: string) => void, disabled?: boolean}> = ({label, value, onChange, disabled}) => (
  <div>
    <label className="block text-sm font-medium text-gray-400">{label}</label>
    <input type="text" value={value} onChange={(e) => onChange(e.target.value)} className="w-full bg-gray-800 rounded p-2 text-sm border border-gray-700 focus:ring-primary focus:border-primary" disabled={disabled}/>
  </div>
);

const OptionToggle: React.FC<{label: string, checked: boolean, onChange: (c: boolean) => void, disabled?: boolean}> = ({label, checked, onChange, disabled}) => (
    <label className="flex items-center justify-between cursor-pointer">
      <span className="text-sm font-medium text-gray-300">{label}</span>
      <div className={`relative inline-flex items-center h-6 rounded-full w-11 transition-colors ${disabled ? 'cursor-not-allowed' : ''}`}>
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          disabled={disabled}
          className="sr-only"
        />
        <div className={`w-11 h-6 rounded-full shadow-inner ${checked && !disabled ? 'bg-primary' : 'bg-gray-700'}`}></div>
        <div className={`absolute left-1 top-1 w-4 h-4 bg-white rounded-full shadow transition-transform ${checked ? 'transform translate-x-5' : ''}`}></div>
      </div>
    </label>
);
