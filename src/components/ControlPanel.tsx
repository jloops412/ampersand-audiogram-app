
import React from 'react';
import type { CustomizationOptions, AuphonicPreset } from '../types';
import { WaveformStyle } from '../types';
import { FileUpload } from './FileUpload';
import { GenerateIcon, LoaderIcon } from './icons';

interface ControlPanelProps {
  options: CustomizationOptions;
  setOptions: React.Dispatch<React.SetStateAction<CustomizationOptions>>;
  onAudioFileChange: (file: File | null) => void;
  onBackgroundImageChange: (file: File | null) => void;
  onTranscriptFileChange: (file: File | null) => void;
  onGenerate: () => void;
  isGenerating: boolean;
  generationProgress: number;
  audioFileName: string | null;
  backgroundImageName: string | null;
  transcriptFileName: string | null;
  auphonicToken: string;
  setAuphonicToken: (token: string) => void;
  auphonicPresets: AuphonicPreset[] | null;
  isAuphonicLoading: boolean;
  onAuphonicSubmit: () => void;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  options,
  setOptions,
  onAudioFileChange,
  onBackgroundImageChange,
  onTranscriptFileChange,
  onGenerate,
  isGenerating,
  generationProgress,
  audioFileName,
  backgroundImageName,
  transcriptFileName,
  auphonicToken,
  setAuphonicToken,
  auphonicPresets,
  isAuphonicLoading,
  onAuphonicSubmit,
}) => {
  const handleOptionChange = (
    key: keyof CustomizationOptions,
    value: any
  ) => {
    setOptions((prev) => ({ ...prev, [key]: value }));
  };
  
  const renderWaveformSpecificOptions = () => {
    switch(options.waveformStyle) {
      case WaveformStyle.Line:
      case WaveformStyle.MirroredLine:
        return (
          <>
            <NumberInput label="Line Width" value={options.lineWidth} onChange={(v) => handleOptionChange('lineWidth', v)} min={1} max={50} />
            <SelectInput label="Line Cap" value={options.lineCap} onChange={(v) => handleOptionChange('lineCap', v)} options={['butt', 'round', 'square']} />
          </>
        );
      case WaveformStyle.Bars:
      case WaveformStyle.Equalizer:
        return (
            <>
                <NumberInput label="Bar Width" value={options.barWidth} onChange={(v) => handleOptionChange('barWidth', v)} min={1} max={100} />
                <NumberInput label="Bar Spacing" value={options.barSpacing} onChange={(v) => handleOptionChange('barSpacing', v)} min={0} max={50} />
                <NumberInput label="Bar Count" value={options.barCount} onChange={(v) => handleOptionChange('barCount', v)} min={8} max={512} step={8} />
            </>
        );
      case WaveformStyle.Circle:
        return <NumberInput label="Circle Radius" value={options.circleRadius} onChange={(v) => handleOptionChange('circleRadius', v)} min={10} max={500} />;
      case WaveformStyle.Bricks:
        return (
            <>
                <NumberInput label="Brick Height" value={options.brickHeight} onChange={(v) => handleOptionChange('brickHeight', v)} min={1} max={50} />
                <NumberInput label="Brick Spacing" value={options.brickSpacing} onChange={(v) => handleOptionChange('brickSpacing', v)} min={0} max={20} />
                <NumberInput label="Brick Count" value={options.brickCount} onChange={(v) => handleOptionChange('brickCount', v)} min={10} max={200} />
            </>
        );
      case WaveformStyle.Radial:
        return (
            <>
                <NumberInput label="Inner Radius" value={options.innerRadius} onChange={(v) => handleOptionChange('innerRadius', v)} min={10} max={400} />
                <NumberInput label="Spoke Count" value={options.spokeCount} onChange={(v) => handleOptionChange('spokeCount', v)} min={12} max={720} />
            </>
        );
      case WaveformStyle.Particles:
        return (
            <>
                <NumberInput label="Particle Count" value={options.particleCount} onChange={(v) => handleOptionChange('particleCount', v)} min={100} max={5000} />
                <NumberInput label="Particle Size" value={options.particleSize} onChange={(v) => handleOptionChange('particleSize', v)} min={1} max={20} />
                <NumberInput label="Particle Speed" value={options.particleSpeed} onChange={(v) => handleOptionChange('particleSpeed', v)} min={0.1} max={10} step={0.1}/>
            </>
        );
      default:
        return null;
    }
  }

  return (
    <div className="bg-gray-900 text-white w-96 p-4 space-y-6 overflow-y-auto">
      <h2 className="text-xl font-bold">Audiogram Generator</h2>
      
      {/* Files Section */}
      <CollapsibleSection title="Files">
        <FileUpload id="audio-file" label="Audio File" onFileChange={onAudioFileChange} accept="audio/*" disabled={isGenerating} fileName={audioFileName} />
        <FileUpload id="bg-image-file" label="Background Image (Optional)" onFileChange={onBackgroundImageChange} accept="image/*" disabled={isGenerating} fileName={backgroundImageName}/>
        <FileUpload id="transcript-file" label="Transcript File (Optional)" onFileChange={onTranscriptFileChange} accept=".vtt,.srt" disabled={isGenerating} fileName={transcriptFileName}/>
      </CollapsibleSection>

      {/* Auphonic Section */}
      <CollapsibleSection title="Auphonic Integration (Optional)">
        <p className="text-xs text-gray-400 mb-2">Process your audio with Auphonic for professional quality before generating the video.</p>
        <TextInput label="Auphonic API Token" type="password" value={auphonicToken} onChange={setAuphonicToken} placeholder="Enter your token" disabled={isGenerating}/>
        {auphonicPresets && (
          <SelectInput label="Auphonic Preset" onChange={() => {}} options={auphonicPresets.map(p => ({ label: p.preset_name, value: p.uuid }))} disabled={isGenerating || isAuphonicLoading}/>
        )}
        <button
            onClick={onAuphonicSubmit}
            disabled={!auphonicToken || isGenerating || isAuphonicLoading}
            className="w-full mt-2 bg-orange-600 hover:bg-orange-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-2 px-4 rounded transition-colors flex items-center justify-center"
        >
            {isAuphonicLoading ? <LoaderIcon className="animate-spin w-5 h-5 mr-2" /> : null}
            Process with Auphonic
        </button>
      </CollapsibleSection>

      {/* Customization Section */}
      <CollapsibleSection title="Customization">
        <TextInput label="Overlay Text" value={options.overlayText} onChange={(v) => handleOptionChange('overlayText', v)} placeholder="Text to display"/>
        <ColorInput label="Background Color" value={options.backgroundColor} onChange={(v) => handleOptionChange('backgroundColor', v)} />
      </CollapsibleSection>

      <CollapsibleSection title="Waveform">
          <SelectInput label="Style" value={options.waveformStyle} onChange={(v) => handleOptionChange('waveformStyle', v)} options={Object.values(WaveformStyle)} />
          <ColorInput label="Color" value={options.waveformColor} onChange={(v) => handleOptionChange('waveformColor', v)} />
          <NumberInput label="Opacity" value={options.waveformOpacity} onChange={(v) => handleOptionChange('waveformOpacity', v)} min={0} max={1} step={0.05} />
          <NumberInput label="Amplitude" value={options.amplitude} onChange={(v) => handleOptionChange('amplitude', v)} min={10} max={500} />
          <SelectInput label="Position" value={options.waveformPosition} onChange={(v) => handleOptionChange('waveformPosition', v)} options={['top', 'middle', 'bottom']} />
          <div className="mt-4 pt-4 border-t border-gray-700 space-y-4">
              {renderWaveformSpecificOptions()}
          </div>
      </CollapsibleSection>

      <CollapsibleSection title="Text Display">
          <ColorInput label="Font Color" value={options.fontColor} onChange={(v) => handleOptionChange('fontColor', v)} />
          <NumberInput label="Font Size (px)" value={options.fontSize} onChange={(v) => handleOptionChange('fontSize', v)} min={8} max={200} />
          <TextInput label="Font Family" value={options.fontFamily} onChange={(v) => handleOptionChange('fontFamily', v)} placeholder="e.g., Inter, sans-serif" />
          <SelectInput label="Text Align" value={options.textAlign} onChange={(v) => handleOptionChange('textAlign', v)} options={['left', 'center', 'right']} />
          <SelectInput label="Text Position" value={options.textPosition} onChange={(v) => handleOptionChange('textPosition', v)} options={['top', 'middle', 'bottom']} />
      </CollapsibleSection>

      {/* Generation Button */}
      <div className="pt-4 border-t border-gray-800">
        <button
          onClick={onGenerate}
          disabled={isGenerating}
          className="w-full bg-primary hover:bg-primary-dark disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-3 px-4 rounded transition-colors flex items-center justify-center text-lg"
        >
          {isGenerating ? (
            <>
              <LoaderIcon className="animate-spin w-5 h-5 mr-3" />
              Generating... ({generationProgress.toFixed(0)}%)
            </>
          ) : (
            <>
              <GenerateIcon className="w-5 h-5 mr-3" />
              Generate Video
            </>
          )}
        </button>
      </div>
    </div>
  );
};

// --- Helper Components ---

const CollapsibleSection: React.FC<{ title: string, children: React.ReactNode }> = ({ title, children }) => {
    const [isOpen, setIsOpen] = React.useState(true);
    return (
        <div className="border border-gray-700 rounded-lg">
            <button className="w-full text-left px-4 py-2 bg-gray-800 rounded-t-lg hover:bg-gray-700 focus:outline-none" onClick={() => setIsOpen(!isOpen)}>
                <h3 className="font-semibold">{title}</h3>
            </button>
            {isOpen && <div className="p-4 space-y-4">{children}</div>}
        </div>
    );
};

interface InputProps<T> {
  label: string;
  value: T;
  onChange: (value: T) => void;
  disabled?: boolean;
}

const TextInput: React.FC<InputProps<string> & { type?: string, placeholder?: string }> = ({ label, value, onChange, type = 'text', placeholder, disabled }) => (
    <div>
        <label className="block text-sm font-medium text-gray-400 mb-1">{label}</label>
        <input type={type} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} disabled={disabled} className="w-full bg-gray-800 border border-gray-600 rounded-md px-3 py-2 text-sm focus:ring-primary focus:border-primary"/>
    </div>
);

const NumberInput: React.FC<InputProps<number> & { min?: number, max?: number, step?: number }> = ({ label, value, onChange, min, max, step, disabled }) => (
    <div>
        <label className="block text-sm font-medium text-gray-400 mb-1">{label}</label>
        <input type="number" value={value} onChange={(e) => onChange(parseFloat(e.target.value))} min={min} max={max} step={step} disabled={disabled} className="w-full bg-gray-800 border border-gray-600 rounded-md px-3 py-2 text-sm focus:ring-primary focus:border-primary"/>
    </div>
);

const ColorInput: React.FC<InputProps<string>> = ({ label, value, onChange, disabled }) => (
    <div>
        <label className="block text-sm font-medium text-gray-400 mb-1">{label}</label>
        <input type="color" value={value} onChange={(e) => onChange(e.target.value)} disabled={disabled} className="w-full h-10 bg-gray-800 border border-gray-600 rounded-md p-1"/>
    </div>
);

const SelectInput: React.FC<InputProps<string> & { options: (string | {label: string, value: string})[] }> = ({ label, value, onChange, options, disabled }) => (
    <div>
        <label className="block text-sm font-medium text-gray-400 mb-1">{label}</label>
        <select value={value} onChange={(e) => onChange(e.target.value)} disabled={disabled} className="w-full bg-gray-800 border border-gray-600 rounded-md px-3 py-2 text-sm focus:ring-primary focus:border-primary">
            {options.map(opt => {
                const val = typeof opt === 'string' ? opt : opt.value;
                const label = typeof opt === 'string' ? opt : opt.label;
                return <option key={val} value={val}>{label}</option>
            })}
        </select>
    </div>
);
