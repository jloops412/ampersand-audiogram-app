
interface RunAuphonicProductionParams {
  audioFile: File;
  coverImageFile: File | null;
  generateTranscript: boolean;
  onProgress: (status: string) => void;
}

interface AuphonicResult {
  audioUrl: string;
  transcriptUrl: string | null;
}

const API_BASE_URL = '/api/auphonic';

const delay = (ms: number) => new Promise(res => setTimeout(res, ms));

export async function runAuphonicProduction({
  audioFile,
  coverImageFile,
  generateTranscript,
  onProgress,
}: RunAuphonicProductionParams): Promise<AuphonicResult> {

  // 1. Create FormData and upload to our backend
  onProgress('Uploading files...');
  const formData = new FormData();
  formData.append('audioFile', audioFile);
  if (coverImageFile) {
    formData.append('coverImageFile', coverImageFile);
  }
  formData.append('title', audioFile.name);

  const createResponse = await fetch(`${API_BASE_URL}/productions`, {
    method: 'POST',
    body: formData,
  });

  if (!createResponse.ok) {
    const errorData = await createResponse.json();
    console.error('Auphonic service error:', errorData);
    throw new Error(`Failed to create Auphonic production: ${createResponse.status} ${errorData.error?.details?.error_message || errorData.error}`);
  }

  const production = await createResponse.json();
  const { uuid } = production;

  // 2. Poll for status
  let status = production.status_string;
  while (status !== 'Done') {
    onProgress(status);
    await delay(5000); // Poll every 5 seconds
    
    const statusResponse = await fetch(`${API_BASE_URL}/productions/${uuid}`);
    if (!statusResponse.ok) {
        throw new Error('Failed to get Auphonic production status.');
    }
    const statusData = await statusResponse.json();
    status = statusData.status_string;

    if (status === 'Error') {
        throw new Error(`Auphonic processing failed: ${statusData.error_message}`);
    }
  }

  onProgress('Processing complete. Downloading results...');

  // 3. Download results via our secure proxy
  const audioUrl = `${API_BASE_URL}/productions/${uuid}/download?type=audio`;
  let transcriptUrl: string | null = null;
  
  if (generateTranscript) {
    transcriptUrl = `${API_BASE_URL}/productions/${uuid}/download?type=transcript`;
  }
  
  return { audioUrl, transcriptUrl };
}
