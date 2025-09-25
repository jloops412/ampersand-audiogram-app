// A helper for polling
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

const AUPHONIC_PRESET_UUID = 'LcXbNksM7Li9oBpWAt5o4H';

interface RunProductionParams {
    audioFile: File;
    generateTranscript: boolean;
    onProgress: (message: string) => void;
}

interface AuphonicProductionResult {
    enhancedAudioFile: File;
    transcriptFile: File | null;
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
    generateTranscript,
    onProgress,
}: RunProductionParams): Promise<AuphonicProductionResult> {
    try {
        // --- 1. Create Production and Upload File via Backend Proxy ---
        onProgress('Uploading audio to Auphonic...');
        const formData = new FormData();
        formData.append('input_file', audioFile);
        
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


        // --- 2. Start Production via Backend Proxy ---
        onProgress('Starting Auphonic processing...');
        const startResponse = await fetchWithTimeout(`/api/auphonic/productions/${uuid}/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                preset: AUPHONIC_PRESET_UUID,
                generateTranscript,
            })
        });
        if (!startResponse.ok) throw new Error('Failed to start Auphonic production.');


        // --- 3. Poll for Status via Backend Proxy ---
        let status = '';
        while (status !== 'Done') {
            await sleep(5000); // Poll every 5 seconds
            const statusResponse = await fetchWithTimeout(`/api/auphonic/productions/${uuid}`);
            if (!statusResponse.ok) throw new Error('Failed to get production status.');
            const statusData = await statusResponse.json();
            status = statusData.data.status_string;
            onProgress(`Auphonic status: ${status}...`);
            
            if (status === 'Error' || status === 'Canceled') throw new Error(`Auphonic processing failed with status: ${status}`);
        }

        // --- 4. Get Results via Backend Proxy ---
        onProgress('Downloading enhanced audio...');
        const resultsResponse = await fetchWithTimeout(`/api/auphonic/productions/${uuid}/results`);
        if (!resultsResponse.ok) throw new Error('Failed to get production results.');
        const resultsData = await resultsResponse.json();
        
        const audioUrl = resultsData.data.output_files[0].download_url;
        const audioBlob = await fetch(audioUrl).then(res => res.blob());
        const enhancedAudioFile = new File([audioBlob], `auphonic_${audioFile.name}`, { type: audioBlob.type });

        let transcriptFile: File | null = null;
        if (generateTranscript) {
            onProgress('Downloading transcript...');
            // Find the transcript service (e.g., whisper) in the results
            const transcriptResult = resultsData.data.services.find((s: any) => s.result_files?.vtt);
            const transcriptUrl = transcriptResult?.result_files?.vtt;

            if (transcriptUrl) {
                const transcriptBlob = await fetch(transcriptUrl).then(res => res.blob());
                transcriptFile = new File([transcriptBlob], 'transcript.vtt', { type: 'text/vtt' });
            } else {
                 onProgress('Warning: Transcript was requested but not found in results.');
            }
        }
        
        onProgress('Auphonic processing complete!');

        return {
            enhancedAudioFile,
            transcriptFile,
        };

    } catch (error) {
        console.error("Auphonic service error:", error);
        onProgress('An error occurred with Auphonic.');
        // Re-throw to be caught by the main handler in App.tsx
        throw error;
    }
}
