interface RunAuphonicProductionParams {
    audioFile: File;
    coverImageFile?: File | null;
    generateTranscript: boolean;
    onProgress: (progress: number, message: string) => void;
}

interface AuphonicResult {
    processedAudioFile: File;
    transcriptContent?: string;
}

const POLLING_INTERVAL = 5000; // 5 seconds

async function checkStatus(uuid: string): Promise<any> {
    const response = await fetch(`/api/auphonic/productions/${uuid}`);
    if (!response.ok) {
        throw new Error('Failed to get Auphonic production status.');
    }
    return response.json();
}

export async function runAuphonicProduction({
    audioFile,
    coverImageFile,
    generateTranscript,
    onProgress,
}: RunAuphonicProductionParams): Promise<AuphonicResult> {
    onProgress(0, 'Uploading files to Auphonic...');
    
    // 1. Create Production and Upload Files
    const createFormData = new FormData();
    createFormData.append('audio', audioFile);
    if (coverImageFile) {
        createFormData.append('coverImage', coverImageFile);
    }
    
    const createResponse = await fetch('/api/auphonic/productions', {
        method: 'POST',
        body: createFormData,
    });

    if (!createResponse.ok) {
        const errorData = await createResponse.json();
        throw new Error(`Failed to create Auphonic production: ${errorData.error || createResponse.statusText}`);
    }
    const { uuid } = await createResponse.json();
    onProgress(10, 'Starting production...');

    // 2. Start Production
    const startResponse = await fetch(`/api/auphonic/productions/${uuid}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ generateTranscript }),
    });

    if (!startResponse.ok) {
        const errorData = await startResponse.json();
        throw new Error(`Failed to start Auphonic production: ${errorData.error || startResponse.statusText}`);
    }

    // 3. Poll for Status
    return new Promise((resolve, reject) => {
        const intervalId = setInterval(async () => {
            try {
                const statusData = await checkStatus(uuid);
                const progressPercentage = statusData.progress || 15;
                onProgress(10 + (progressPercentage * 0.7), `Processing... (${statusData.status_string})`);

                if (statusData.status === 3) { // 3 means "Done"
                    clearInterval(intervalId);
                    onProgress(80, 'Downloading processed files...');
                    
                    // 4. Download Results
                    const audioResultUrl = statusData.results.find((r: any) => r.output_basename.endsWith('.wav'))?.download_url;
                    
                    if (!audioResultUrl) {
                       throw new Error('Could not find processed audio file in Auphonic results.');
                    }
                    
                    const audioResponse = await fetch(`/api/auphonic/download?url=${encodeURIComponent(audioResultUrl)}`);
                    if (!audioResponse.ok) throw new Error('Failed to download processed audio.');
                    const audioBlob = await audioResponse.blob();
                    const processedAudioFile = new File([audioBlob], `auphonic_${audioFile.name}.wav`, { type: 'audio/wav' });

                    let transcriptContent: string | undefined = undefined;
                    if (generateTranscript) {
                        const transcriptUrl = statusData.results.find((r: any) => r.output_basename.endsWith('.vtt'))?.download_url;
                        if (transcriptUrl) {
                            const transcriptResponse = await fetch(`/api/auphonic/download?url=${encodeURIComponent(transcriptUrl)}`);
                            if(transcriptResponse.ok) {
                                transcriptContent = await transcriptResponse.text();
                            }
                        } else {
                            console.warn("Transcript generation was enabled, but no VTT file was found in results.");
                        }
                    }

                    onProgress(100, 'Processing complete.');
                    resolve({ processedAudioFile, transcriptContent });
                } else if (statusData.status > 3) { // Error states
                    clearInterval(intervalId);
                    reject(new Error(`Auphonic production failed with status: ${statusData.status_string}`));
                }
            } catch (error) {
                clearInterval(intervalId);
                reject(error);
            }
        }, POLLING_INTERVAL);
    });
}
