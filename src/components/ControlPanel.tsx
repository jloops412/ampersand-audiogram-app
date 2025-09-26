import React from 'react';
import type { CustomizationOptions, LineCap, TextAlign, TextPosition } from '../types';
import { WaveformStyle } from '../types';
import { FileUpload } from './FileUpload';
import { GenerateIcon } from './icons';
import { GOOGLE_FONTS } from '../constants';

interface ControlPanelProps {
  options: CustomizationOptions;
  setOptions: React.Dispatch<React.SetStateAction<CustomizationOptions>>;
  onAudioFileChange: (file: File | null) => void;
  onBackgroundImageChange: (file: File | null) => void;
  onTranscriptFileChange: (file: File | null) => void;
  onOverlayTextChange: (text: string) => void;
  onGenerateVideo: () => void;
  isGenerating: boolean;
  audioFileName?: string;
  transcriptFileName?: string;
}

interface OptionWrapperProps {
  title: string;
  children: React.ReactNode;
  className?: string;
}

const OptionWrapper: React.FC<OptionWrapperProps> = ({ title, children, className }) => (
  <div className={`mb-4 ${className}`}>
    <label className="block text-sm font-medium text-gray-400 mb-2">{title}</label>
    {children}
  </div>
);

interface ToggleSwitchProps {
  label: string;
  enabled: boolean;
  onChange: (enabled: boolean) => void;
  disabled?: boolean;
}

const ToggleSwitch: React.FC<ToggleSwitchProps> = ({ label, enabled, onChange, disabled }) => {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-gray-300">{label}</span>
      <button
        type="button"
        onClick={() => onChange(!enabled)}
        disabled={disabled}
        className={`${
          enabled ? 'bg-primary' : 'bg-gray-700'
        } relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed`}
        aria-pressed={enabled}
      >
        <span
          aria-hidden="true"
          className={`${
            enabled ? 'translate-x-5' : 'translate-x-0'
          } pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out`}
        />
      </button>
    </div>
  );
};


const lineCapOptions: { value: LineCap; label: string }[] = [
    { value: 'round', label: 'Round' },
    { value: 'butt', label: 'Butt' },
    { value: 'square', label: 'Square' },
];

const textAlignOptions: { value: TextAlign; label: string }[] = [
    { value: 'left', label: 'Left' },
    { value: 'center', label: 'Center' },
    { value: 'right', label: 'Right' },
];

const textPositionOptions: { value: TextPosition; label: string }[] = [
    { value: 'top', label: 'Top' },
    { value: 'middle', label: 'Middle' },
    { value: 'bottom', label: 'Bottom' },
];

const lineBasedStyles = [WaveformStyle.Line, WaveformStyle.MirroredLine, WaveformStyle.Circle, WaveformStyle.Radial];
const barBasedStyles = [WaveformStyle.Bars, WaveformStyle.Equalizer];
const positionableStyles = [WaveformStyle.Line, WaveformStyle.MirroredLine, WaveformStyle.Bars, WaveformStyle.Bricks];

export const ControlPanel: React.FC<ControlPanelProps> = ({
  options,
  setOptions,
  onAudioFileChange,
  onBackgroundImageChange,
  onTranscriptFileChange,
  onOverlayTextChange,
  onGenerateVideo,
  isGenerating,
  audioFileName,
  transcriptFileName,
}) => {
  const handleOptionChange = <K extends keyof CustomizationOptions,>(
    key: K,
    value: CustomizationOptions[K]
  ) => {
    setOptions(prev => ({ ...prev, [key]: value }));
  };

  const handleEnhanceChange = (enabled: boolean) => {
    handleOptionChange('enhanceWithAuphonic', enabled);
    // If user disables enhancement, also disable transcript generation
    if (!enabled) {
      handleOptionChange('generateTranscript', false);
    }
  };

  // User can't use Auphonic if they've manually uploaded a transcript or are using static text
  const isAuphonicDisabled = !!transcriptFileName || !!options.overlayText;

  return (
    <div className="bg-gray-900 p-6 rounded-xl shadow-lg border border-gray-800">
      <h2 className="text-2xl font-bold mb-6 text-white border-b border-gray-700 pb-4">Customize</h2>
      
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold text-primary mb-3">Files</h3>
          <FileUpload
            id="audio-upload"
            label="Upload Audio"
            onFileChange={onAudioFileChange}
            accept="audio/*"
            fileName={audioFileName}
            disabled={isGenerating}
          />
          <FileUpload
            id="bg-image-upload"
            label="Upload Background (Optional)"
            onFileChange={onBackgroundImageChange}
            accept="image/*"
            disabled={isGenerating}
            className="mt-4"
          />
        </div>
        
        <div>
            <h3 className="text-lg font-semibold text-primary mb-3">Audio Processing</h3>
            <div className="space-y-3 p-4 bg-gray-800 rounded-lg">
                <ToggleSwitch
                    label="Enhance Audio with Auphonic"
                    enabled={options.enhanceWithAuphonic}
                    onChange={handleEnhanceChange}
                    disabled={isGenerating || isAuphonicDisabled}
                />
                 <ToggleSwitch
                    label="Generate Transcript"
                    enabled={options.generateTranscript}
                    onChange={(value) => handleOptionChange('generateTranscript', value)}
                    disabled={isGenerating || !options.enhanceWithAuphonic || isAuphonicDisabled}
                />
                <p className="text-xs text-gray-500 pt-2">
                    {isAuphonicDisabled 
                        ? "Auphonic is disabled when using a manual transcript or static text." 
                        : "Uses Auphonic to professionally process your audio. Requires a backend server."
                    }
                </p>
            </div>
        </div>

        <div className={options.enhanceWithAuphonic ? 'opacity-50 pointer-events-none' : 'transition-opacity'}>
            <h3 className="text-lg font-semibold text-primary mb-3">Text & Transcript</h3>
            <FileUpload
                id="transcript-upload"
                label="Upload Transcript (Optional)"
                onFileChange={onTranscriptFileChange}
                accept=".srt,.vtt"
                disabled={isGenerating || options.enhanceWithAuphonic}
                fileName={transcriptFileName}
            />
            <OptionWrapper title="Static Text Overlay">
                 <textarea
                    value={options.overlayText}
                    onChange={(e) => onOverlayTextChange(e.target.value)}
                    disabled={isGenerating || !!transcriptFileName || options.enhanceWithAuphonic}
                    placeholder={transcriptFileName ? 'Transcript file is active' : (options.enhanceWithAuphonic ? 'Auphonic transcript will be used' : 'Enter text to display')}
                    className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-white focus:ring-2 focus:ring-primary focus:border-primary disabled:bg-gray-800/50"
                    rows={2}
                />
            </OptionWrapper>
            <OptionWrapper title="Font Family">
                 <select
                    value={options.fontFamily}
                    onChange={(e) => handleOptionChange('fontFamily', e.target.value)}
                    disabled={isGenerating}
                    className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-white focus:ring-2 focus:ring-primary focus:border-primary"
                    style={{ fontFamily: options.fontFamily }}
                 >
                    {GOOGLE_FONTS.map(font => (
                        <option key={font} value={font} style={{ fontFamily: font }}>{font}</option>
                    ))}
                </select>
            </OptionWrapper>
             <div className="grid grid-cols-2 gap-4">
                <OptionWrapper title="Font Color">
                    <input
                        type="color"
                        value={options.fontColor}
                        onChange={(e) => handleOptionChange('fontColor', e.target.value)}
                        disabled={isGenerating}
                        className="w-full h-10 p-1 bg-gray-800 border border-gray-700 rounded-md cursor-pointer"
                    />
                </OptionWrapper>
                <OptionWrapper title={`Font Size: ${options.fontSize}px`}>
                     <input type="range" min="12" max="200" value={options.fontSize} onChange={(e) => handleOptionChange('fontSize', Number(e.target.value))} disabled={isGenerating} className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary mt-3"/>
                </OptionWrapper>
             </div>
              <div className="grid grid-cols-2 gap-4">
                 <OptionWrapper title="Text Align">
                    <select value={options.textAlign} onChange={(e) => handleOptionChange('textAlign', e.target.value as TextAlign)} disabled={isGenerating} className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-white focus:ring-2 focus:ring-primary focus:border-primary">
                        {textAlignOptions.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                    </select>
                </OptionWrapper>
                <OptionWrapper title="Vertical Position">
                    <select value={options.textPosition} onChange={(e) => handleOptionChange('textPosition', e.target.value as TextPosition)} disabled={isGenerating} className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-white focus:ring-2 focus:ring-primary focus:border-primary">
                        {textPositionOptions.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                    </select>
                </OptionWrapper>
              </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-primary mb-3">Style</h3>
           <OptionWrapper title="Waveform Style">
            <select
              value={options.waveformStyle}
              onChange={(e) => handleOptionChange('waveformStyle', e.target.value as WaveformStyle)}
              disabled={isGenerating}
              className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-white focus:ring-2 focus:ring-primary focus:border-primary"
            >
              {Object.values(WaveformStyle).map(style => (
                <option key={style} value={style}>{style}</option>
              ))}
            </select>
          </OptionWrapper>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-primary mb-3">Colors</h3>
           <div className="grid grid-cols-2 gap-4">
              <OptionWrapper title="Waveform">
                <input
                  type="color"
                  value={options.waveformColor}
                  onChange={(e) => handleOptionChange('waveformColor', e.target.value)}
                  disabled={isGenerating}
                  className="w-full h-10 p-1 bg-gray-800 border border-gray-700 rounded-md cursor-pointer"
                />
              </OptionWrapper>
              <OptionWrapper title="Background">
                <input
                  type="color"
                  value={options.backgroundColor}
                  onChange={(e) => handleOptionChange('backgroundColor', e.target.value)}
                  disabled={isGenerating}
                  className="w-full h-10 p-1 bg-gray-800 border border-gray-700 rounded-md cursor-pointer"
                />
              </OptionWrapper>
           </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-primary mb-3">Waveform Settings</h3>
          <OptionWrapper title={`Amplitude: ${options.amplitude}`}>
            <input
              type="range" min="10" max="500"
              value={options.amplitude}
              onChange={(e) => handleOptionChange('amplitude', Number(e.target.value))}
              disabled={isGenerating}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary"
            />
          </OptionWrapper>
          <OptionWrapper title={`Opacity: ${Math.round(options.waveformOpacity * 100)}%`}>
            <input
              type="range" min="0" max="1" step="0.05"
              value={options.waveformOpacity}
              onChange={(e) => handleOptionChange('waveformOpacity', Number(e.target.value))}
              disabled={isGenerating}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary"
            />
          </OptionWrapper>

          {positionableStyles.includes(options.waveformStyle) && (
             <OptionWrapper title="Waveform Position">
                <select value={options.waveformPosition} onChange={(e) => handleOptionChange('waveformPosition', e.target.value as TextPosition)} disabled={isGenerating} className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-white focus:ring-2 focus:ring-primary focus:border-primary">
                    {textPositionOptions.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                </select>
            </OptionWrapper>
          )}

          {lineBasedStyles.includes(options.waveformStyle) && (
             <>
                <OptionWrapper title={`Line Width: ${options.lineWidth}`}>
                    <input
                        type="range" min="1" max="20"
                        value={options.lineWidth}
                        onChange={(e) => handleOptionChange('lineWidth', Number(e.target.value))}
                        disabled={isGenerating}
                        className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary"
                    />
                </OptionWrapper>
                <OptionWrapper title="Line Cap">
                     <select
                        value={options.lineCap}
                        onChange={(e) => handleOptionChange('lineCap', e.target.value as LineCap)}
                        disabled={isGenerating}
                        className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-white focus:ring-2 focus:ring-primary focus:border-primary"
                     >
                        {lineCapOptions.map(cap => (
                            <option key={cap.value} value={cap.value}>{cap.label}</option>
                        ))}
                    </select>
                </OptionWrapper>
             </>
          )}

          {barBasedStyles.includes(options.waveformStyle) && (
            <>
              <OptionWrapper title={`Bar Count: ${options.barCount}`}>
                <input type="range" min="32" max="512" step="16" value={options.barCount} onChange={(e) => handleOptionChange('barCount', Number(e.target.value))} disabled={isGenerating} className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary"/>
              </OptionWrapper>
              <OptionWrapper title={`Bar Width: ${options.barWidth}`}>
                <input type="range" min="1" max="50" value={options.barWidth} onChange={(e) => handleOptionChange('barWidth', Number(e.target.value))} disabled={isGenerating} className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary"/>
              </OptionWrapper>
               <OptionWrapper title={`Bar Spacing: ${options.barSpacing}`}>
                <input type="range" min="0" max="20" value={options.barSpacing} onChange={(e) => handleOptionChange('barSpacing', Number(e.target.value))} disabled={isGenerating} className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary"/>
              </OptionWrapper>
            </>
          )}

          {options.waveformStyle === WaveformStyle.Circle && (
            <OptionWrapper title={`Circle Radius: ${options.circleRadius}`}>
               <input type="range" min="50" max="400" value={options.circleRadius} onChange={(e) => handleOptionChange('circleRadius', Number(e.target.value))} disabled={isGenerating} className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary"/>
            </OptionWrapper>
          )}
          
          {options.waveformStyle === WaveformStyle.Bricks && (
            <>
              <OptionWrapper title={`Brick Count: ${options.brickCount}`}>
                <input type="range" min="20" max="200" value={options.brickCount} onChange={(e) => handleOptionChange('brickCount', Number(e.target.value))} disabled={isGenerating} className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary"/>
              </OptionWrapper>
              <OptionWrapper title={`Brick Height: ${options.brickHeight}`}>
                <input type="range" min="1" max="20" value={options.brickHeight} onChange={(e) => handleOptionChange('brickHeight', Number(e.target.value))} disabled={isGenerating} className="w-full h-2 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-primary"/>
              </OptionWrapper>
              <OptionWrapper title={`Brick Spacing: ${options.brickSpacing}`}>
                <input type="range" min="0" max="10" value={options.brickSpacing} onChange={(e) => handleOptionChange('brickSpacing', Number(e.target.value))} disabled={isGenerating} className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary"/>
              </OptionWrapper>
            </>
          )}

          {options.waveformStyle === WaveformStyle.Radial && (
            <>
              <OptionWrapper title={`Spoke Count: ${options.spokeCount}`}>
                <input type="range" min="20" max="720" value={options.spokeCount} onChange={(e) => handleOptionChange('spokeCount', Number(e.target.value))} disabled={isGenerating} className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary"/>
              </OptionWrapper>
              <OptionWrapper title={`Inner Radius: ${options.innerRadius}`}>
                <input type="range" min="0" max="300" value={options.innerRadius} onChange={(e) => handleOptionChange('innerRadius', Number(e.target.value))} disabled={isGenerating} className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary"/>
              </OptionWrapper>
            </>
          )}

          {options.waveformStyle === WaveformStyle.Particles && (
            <>
              <OptionWrapper title={`Particle Count: ${options.particleCount}`}>
                <input type="range" min="50" max="1000" value={options.particleCount} onChange={(e) => handleOptionChange('particleCount', Number(e.target.value))} disabled={isGenerating} className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary"/>
              </OptionWrapper>
              <OptionWrapper title={`Particle Size: ${options.particleSize}`}>
                <input type="range" min="0.5" max="10" step="0.5" value={options.particleSize} onChange={(e) => handleOptionChange('particleSize', Number(e.target.value))} disabled={isGenerating} className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary"/>
              </OptionWrapper>
              <OptionWrapper title={`Particle Speed: ${options.particleSpeed}`}>
                <input type="range" min="0.5" max="10" step="0.5" value={options.particleSpeed} onChange={(e) => handleOptionChange('particleSpeed', Number(e.target.value))} disabled={isGenerating} className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary"/>
              </OptionWrapper>
            </>
          )}
        </div>
      </div>
      
      <button
        onClick={onGenerateVideo}
        disabled={isGenerating}
        className="mt-8 w-full flex items-center justify-center gap-2 bg-primary text-gray-950 font-bold py-3 px-4 rounded-md hover:bg-opacity-90 transition-all transform hover:scale-105 disabled:bg-gray-600 disabled:cursor-not-allowed disabled:scale-100"
      >
        <GenerateIcon className="w-5 h-5" />
        Generate Video
      </button>
    </div>
  );
};