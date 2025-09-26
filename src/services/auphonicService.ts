
const AUPHONIC_API_BASE = 'https://auphonic.com/api';

/**
 * Fetches Auphonic production presets for a given access token.
 * @param {string} accessToken - The Auphonic OAuth2 access token.
 * @returns {Promise<Array<{uuid: string, preset_name: string}>>} A list of presets.
 */
export async function getAuphonicPresets(accessToken: string): Promise<Array<{uuid: string, preset_name: string}>> {
  if (!accessToken) {
    console.warn('Auphonic access token is not provided.');
    return [];
  }

  try {
    const response = await fetch(`${AUPHONIC_API_BASE}/presets.json`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Auphonic authentication failed. Please check your access token.');
      }
      throw new Error(`Failed to fetch Auphonic presets. Status: ${response.status}`);
    }

    const data = await response.json();
    return data.data || [];
  } catch (error) {
    console.error('Error fetching Auphonic presets:', error);
    // Return empty array on error to allow the app to function without presets
    return [];
  }
}
