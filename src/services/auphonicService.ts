
import { AuphonicPreset } from '../types';

const MOCK_PRESETS: AuphonicPreset[] = [
    { uuid: 'preset-1', preset_name: 'Podcast Master' },
    { uuid: 'preset-2', preset_name: 'Voice Over Clean' },
    { uuid: 'preset-3', preset_name: 'Music Bed Enhance' },
];

/**
 * Fetches Auphonic production presets.
 * This is a mock implementation.
 * @returns {Promise<AuphonicPreset[]>} A promise that resolves with an array of presets.
 */
export async function fetchAuphonicPresets(): Promise<AuphonicPreset[]> {
    console.log('Fetching Auphonic presets (mock)...');
    return new Promise(resolve => {
        setTimeout(() => {
            resolve(MOCK_PRESETS);
        }, 500);
    });
}
