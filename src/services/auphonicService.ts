import type { AuphonicProcessingOptions } from '../types';

interface RunProductionParams {
  audioFile: File;
  generateTranscript: boolean;
  auphonicProcessing: AuphonicProcessingOptions;
  onProgress: (message: string) => void;
}

interface RunProductionResult {
  enhancedAudioFile: File;
  transcriptFile: File | null;
}

// Helper to poll for production status
const poll = async <T>(
    fn: () => Promise<T>, 
    validate: (result: T) => boolean, 
    ms: number
): Promise<T> => {
    let result = await fn();
    while (validate(result)) {
        await new Promise(resolve => setTimeout(resolve, ms));
        result = await fn();
    }
    return result;
};

export async function runProduction({
  audioFile,
  generateTranscript,
  auphonicProcessing,
  onProgress,
}: RunProductionParams): Promise<RunProductionResult> {

    onProgress('Uploading audio to Auphonic...');

    const formData = new FormData();
    formData.append('audioFile', audioFile);
    formData.append('generateTranscript', String(generateTranscript));
    formData.append('auphonicProcessing', JSON.stringify(auphonicProcessing));
    
    // 1. Create Production
    let createResponse;
    try {
        createResponse = await fetch('/api/auphonic/productions', {
            method: 'POST',
            body: formData,
        });
    } catch (error) {
        console.error('Network error creating Auphonic production:', error);
        throw new Error('Could not connect to the server for Auphonic processing. Please ensure the backend is running.');
    }
    
    if (!createResponse.ok) {
        const errorData = await createResponse.json().catch(() => ({ message: `Auphonic production request failed with status ${createResponse.status}` }));
        throw new Error(errorData.message || 'Failed to start Auphonic production.');
    }
    
    const { uuid } = await createResponse.json();
    if (!uuid) {
        throw new Error('Did not receive a valid production ID from the server.');
    }
    
    onProgress('Processing audio with Auphonic...');
    
    // 2. Poll for status
    const finalStatus = await poll(
        async () => {
            const statusResponse = await fetch(`/api/auphonic/productions/${uuid}`);
            if (!statusResponse.ok) {
                console.error(`Failed to get Auphonic status for ${uuid}: ${statusResponse.status}`);
                return { status_string: 'Polling Error' };
            }
            const data = await statusResponse.json();
            onProgress(`Auphonic status: ${data.status_string}`);
            return data;
        },
        (result: any) => ['Done', 'Error', 'Terminated', 'Polling Error'].indexOf(result.status_string) === -1,
        5000 // Poll every 5 seconds
    );
    
    if (finalStatus.status_string !== 'Done') {
        throw new Error(`Auphonic production failed with status: ${finalStatus.status_string}`);
    }
    
    onProgress('Downloading processed files...');
    
    // 3. Download results
    const resultsResponse = await fetch(`/api/auphonic/productions/${uuid}/result`);
    if (!resultsResponse.ok) {
        throw new Error('Failed to download Auphonic results.');
    }
    
    const { audioUrl, transcriptUrl, originalFilename } = await resultsResponse.json();
    
    if (!audioUrl || !originalFilename) {
        throw new Error('Server did not provide valid result URLs for Auphonic production.');
    }

    const audioBlob = await fetch(audioUrl).then(res => {
        if (!res.ok) throw new Error('Failed to download enhanced audio file.');
        return res.blob();
    });
    
    const nameParts = originalFilename.split('.');
    const extension = nameParts.pop() || 'dat';
    const baseName = nameParts.join('.');
    const enhancedAudioFile = new File([audioBlob], `${baseName}_auphonic.${extension}`, { type: audioBlob.type });
    
    let transcriptFile: File | null = null;
    if (transcriptUrl) {
        onProgress('Downloading transcript...');
        const transcriptBlob = await fetch(transcriptUrl).then(res => {
            if (!res.ok) throw new Error('Failed to download transcript file.');
            return res.blob();
        });
        const transcriptExtension = transcriptUrl.includes('.srt') ? 'srt' : 'vtt';
        transcriptFile = new File([transcriptBlob], `${baseName}.${transcriptExtension}`, { type: transcriptBlob.type });
    }

    onProgress('Auphonic processing complete!');
    
    return {
        enhancedAudioFile,
        transcriptFile,
    };
}
