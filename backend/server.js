import express from 'express';
import fetch from 'node-fetch';
import { formidable } from 'formidable';
import { readFileSync } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const app = express();
const port = process.env.PORT || 8080;

const AUPHONIC_API_KEY = process.env.AUPHONIC_API_KEY;
const AUPHONIC_API_BASE = 'https://auphonic.com/api';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

if (!AUPHONIC_API_KEY) {
    console.error("FATAL ERROR: AUPHONIC_API_KEY environment variable is not set.");
    process.exit(1);
}
const AUTH_HEADER = 'Basic ' + Buffer.from(`api:${AUPHONIC_API_KEY}`).toString('base64');

app.use(express.json());

// --- Auphonic API Proxy Endpoints ---

// 1. Create Production & Upload File (Combined)
app.post('/api/auphonic/productions', async (req, res) => {
    const form = formidable({});
    form.parse(req, async (err, fields, files) => {
        if (err || !files.input_file) {
            console.error('Form parsing error or file missing:', err);
            return res.status(500).send('Form parsing error or input_file missing');
        }
        
        const inputFile = files.input_file[0];
        
        try {
            const fileBuffer = readFileSync(inputFile.filepath);
            
            const formData = new FormData();
            // Append the raw Buffer directly, avoiding the incompatible Blob constructor.
            formData.append('input_file', fileBuffer, inputFile.originalFilename);
            
            const metadata = {
                title: inputFile.originalFilename || 'Audiogram Production',
            };
            formData.append('metadata', JSON.stringify(metadata));

            // Do not set Content-Type header manually for multipart/form-data.
            // Let node-fetch set it automatically with the correct boundary.
            const createRes = await fetch(`${AUPHONIC_API_BASE}/productions.json`, {
                method: 'POST',
                headers: { 'Authorization': AUTH_HEADER },
                body: formData,
            });

            if (!createRes.ok) {
                const errorText = await createRes.text();
                throw new Error(`Auphonic Create/Upload Error: ${createRes.status} ${errorText}`);
            }
            
            const { data: { uuid } } = await createRes.json();
            
            res.status(200).json({ uuid });
        } catch (error) {
            console.error('Auphonic create/upload error:', error);
            res.status(500).send(error.message);
        }
    });
});

// 2. Start Production
app.post('/api/auphonic/productions/:uuid/start', async (req, res) => {
    const { uuid } = req.params;
    const { generateTranscript, auphonicProcessing } = req.body;
    
    // Build the payload for the Auphonic API
    const payload = {
        preset: '', // Use an empty preset to define algorithms manually
        output_files: [ { format: "wav" } ], // ensure we get a high-quality audio file back
        algorithms: {
            // Map frontend options to the correct Auphonic API parameters
            leveler: auphonicProcessing.adaptiveLeveler,
            denoise: auphonicProcessing.noiseAndHumReduction,
            // If amount is 0, send null for 'auto' mode
            denoiseamount: auphonicProcessing.noiseReductionAmount > 0 ? auphonicProcessing.noiseReductionAmount : null,
            hipfilter: auphonicProcessing.filtering,
            normloudness: !!auphonicProcessing.loudnessTarget, // Enable if target is set
        },
        loudness_target: auphonicProcessing.loudnessTarget,
    };

    if (generateTranscript) {
        payload.services = { whisper: true };
    }

    try {
        const apiRes = await fetch(`${AUPHONIC_API_BASE}/production/${uuid}/start.json`, {
            method: 'POST',
            headers: { 'Authorization': AUTH_HEADER, 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!apiRes.ok) {
            const errorText = await apiRes.text();
            console.error('Auphonic Start API Error:', errorText);
            throw new Error(`Auphonic Start Error: ${errorText}`);
        }
        res.status(200).json(await apiRes.json());
    } catch (error) {
        console.error('Auphonic start error:', error);
        res.status(500).send(error.message);
    }
});

// 3 & 4. Get Status / Get Results
app.get('/api/auphonic/productions/:uuid/:action?', async (req, res) => {
    const { uuid, action } = req.params;
    const endpoint = action === 'results' ? `${AUPHONIC_API_BASE}/production/${uuid}.json?get_results=true` : `${AUPHONIC_API_BASE}/production/${uuid}.json`;
    
    try {
        const apiRes = await fetch(endpoint, { headers: { 'Authorization': AUTH_HEADER } });
        if (!apiRes.ok) throw new Error(`Auphonic Get Status/Results Error: ${await apiRes.text()}`);
        res.status(200).json(await apiRes.json());
    } catch (error) {
         console.error('Auphonic get status/results error:', error);
         res.status(500).send(error.message);
    }
});

// --- Serve Frontend Files ---
app.use(express.static(path.join(__dirname, '../dist')));

app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, '../dist/index.html'));
});

app.listen(port, () => console.log(`Server listening on port ${port}`));