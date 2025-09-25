
import React, { useRef, useState } from 'react';
import { UploadIcon } from './icons';

interface FileUploadProps {
  id: string;
  label: string;
  onFileChange: (file: File | null) => void;
  accept: string;
  disabled?: boolean;
  className?: string;
  fileName?: string;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  id,
  label,
  onFileChange,
  accept,
  disabled,
  className,
  fileName
}) => {
  const [localFileName, setLocalFileName] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files ? event.target.files[0] : null;
    onFileChange(file);
    setLocalFileName(file?.name || null);
  };
  
  const currentFileName = fileName || localFileName;

  return (
    <div className={className}>
      <label htmlFor={id} className="block text-sm font-medium text-gray-400 mb-1">{label}</label>
      <div
        className={`relative flex items-center justify-center px-3 py-2 border-2 border-dashed rounded-md transition-colors ${disabled ? 'bg-gray-800 cursor-not-allowed' : 'border-gray-700 hover:border-primary bg-gray-800 cursor-pointer'}`}
        onClick={() => !disabled && inputRef.current?.click()}
      >
        <div className="flex items-center text-sm text-gray-400">
          <UploadIcon className="w-5 h-5 mr-2" />
          <span className="font-medium text-primary truncate max-w-[200px]">
            {currentFileName ? currentFileName : 'Choose a file'}
          </span>
        </div>
        <input
          id={id}
          ref={inputRef}
          type="file"
          accept={accept}
          onChange={handleFileChange}
          className="sr-only"
          disabled={disabled}
        />
      </div>
    </div>
  );
};
