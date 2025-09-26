// A helper for polling
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

interface RunProductionParams {
    audioFile: File;
    coverImageFile: File | null;
    generateTranscript: boolean;
    onProgress: (message: string) => void;
}

interface AuphonicProductionResult {
    enhancedAudioFile: File;
    transcriptText: string | null;
}

/**
 * A wrapper for the fetch API that includes a timeout.
 * @param resource The URL to fetch.
 * @param options Fetch options.
 * @param timeout Timeout in milliseconds.
 * @returns A Promise that resolves to the Response.
 */
async function fetchWithTimeout(resource: RequestInfo, options: RequestInit = {}, timeout = 60000) {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    const response = await fetch(resource, {
        ...options,
        signal: controller.signal  
    });
    clearTimeout(id);
    return response;
}

/**
 * Manages the entire Auphonic production lifecycle through a backend proxy.
 * This includes uploading, starting, polling for status, and downloading results.
 */
export async function runProduction({
    audioFile,
    coverImageFile,
    generateTranscript,
    onProgress,
}: RunProductionParams): Promise<AuphonicProductionResult> {
    try {
        // --- 1. Create Production and Upload File via Backend Proxy ---
        onProgress('Uploading to Auphonic...');
        const formData = new FormData();
        formData.append('input_file', audioFile);
        if (coverImageFile) {
            formData.append('image', coverImageFile);
        }
        formData.append('generateTranscript', String(generateTranscript));
        
        const createResponse = await fetchWithTimeout('/api/auphonic/productions', {
            method: 'POST',
            body: formData,
        });

        if (!createResponse.ok) {
            const errorText = await createResponse.text();
            throw new Error(`Failed to create Auphonic production: ${createResponse.status} ${errorText}`);
        }
        const { uuid } = await createResponse.json();
        if (!uuid) throw new Error('Did not receive a UUID from the backend proxy.');


        // --- 2. Poll for Status via Backend Proxy ---
        let status = '';
        let resultsData: any = null;

        while (status !== 'Done') {
            await sleep(5000); // Poll every 5 seconds
            const statusResponse = await fetchWithTimeout(`/api/auphonic/productions/${uuid}`);
            if (!statusResponse.ok) throw new Error('Failed to get production status.');
            const statusData = await statusResponse.json();
            status = statusData.data.status_string;
            onProgress(`Auphonic status: ${status}...`);
            
            if (status === 'Error' || status === 'Canceled') {
                throw new Error(`Auphonic processing failed with status: ${status}`);
            }
            if (status === 'Done') {
                resultsData = statusData.data;
            }
        }

        // --- 3. Get Results via Secure Backend Download Proxy ---
        onProgress('Downloading enhanced audio...');
        
        const audioUrl = resultsData.output_files[0].download_url;
        const audioDownloadResponse = await fetch(`/api/auphonic/download?url=${encodeURIComponent(audioUrl)}`);
        if (!audioDownloadResponse.ok) throw new Error('Failed to download enhanced audio file.');

        const audioBlob = await audioDownloadResponse.blob();
        const enhancedAudioFile = new File([audioBlob], `auphonic_${audioFile.name}`, { type: audioBlob.type });

        let transcriptText: string | null = null;
        if (generateTranscript) {
            onProgress('Downloading transcript...');
            const transcriptResult = resultsData.services.find((s: any) => s.result_files?.vtt);
            const transcriptUrl = transcriptResult?.result_files?.vtt;

            if (transcriptUrl) {
                const transcriptDownloadResponse = await fetch(`/api/auphonic/download?url=${encodeURIComponent(transcriptUrl)}`);
                if (!transcriptDownloadResponse.ok) {
                    onProgress('Warning: Failed to download transcript file.');
                } else {
                    transcriptText = await transcriptDownloadResponse.text();
                }
            } else {
                 onProgress('Warning: Transcript was requested but not found in results.');
            }
        }
        
        onProgress('Auphonic processing complete!');

        return {
            enhancedAudioFile,
            transcriptText,
        };

    } catch (error) {
        console.error("Auphonic service error:", error);
        onProgress('An error occurred with Auphonic.');
        throw error;
    }
}