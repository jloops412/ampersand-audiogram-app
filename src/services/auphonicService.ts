
import type { AuphonicPreset, AuphonicProduction } from '../types';

const AUPHONIC_API_BASE = 'https://auphonic.com/api';

/**
 * Fetches the user's presets from Auphonic.
 * @param token - The Auphonic API token.
 * @returns A promise that resolves to an array of presets.
 */
export async function getAuphonicPresets(token: string): Promise<AuphonicPreset[]> {
  if (!token) {
    throw new Error('Auphonic API token is required.');
  }

  const response = await fetch(`${AUPHONIC_API_BASE}/presets.json`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ message: response.statusText }));
    throw new Error(`Failed to fetch Auphonic presets: ${errorData.error_message || response.statusText}`);
  }

  const result = await response.json();
  return result.data as AuphonicPreset[];
}

interface CreateProductionParams {
  preset: string;
  title: string;
  inputFile: File;
  imageFile?: File | null;
  token: string;
}

/**
 * Creates a new production in Auphonic.
 * @param params - The parameters for creating the production.
 * @returns A promise that resolves to the created production data.
 */
export async function createAuphonicProduction({
  preset,
  title,
  inputFile,
  imageFile,
  token
}: CreateProductionParams): Promise<AuphonicProduction> {
    if (!token) {
        throw new Error('Auphonic API token is required.');
    }

    const metadata = {
        preset,
        title,
        // Add other metadata fields if needed
    };

    const formData = new FormData();
    formData.append('metadata', JSON.stringify(metadata));
    formData.append('input_file', inputFile);
    if (imageFile) {
        formData.append('image', imageFile);
    }
    
    const response = await fetch(`${AUPHONIC_API_BASE}/productions.json`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
        },
        body: formData,
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: response.statusText }));
        throw new Error(`Failed to create Auphonic production: ${errorData.error_message || response.statusText}`);
    }

    const result = await response.json();
    return result.data as AuphonicProduction;
}
