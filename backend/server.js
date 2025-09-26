import express from 'express';
import cors from 'cors';
import formidable from 'formidable';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import fetch from 'node-fetch';
import FormData from 'form-data';

const app = express();
const PORT = process.env.PORT || 8080;

// Middleware
app.use(cors());
app.use(express.json());

// --- Static File Serving ---
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const buildPath = path.join(__dirname, '..', 'dist');
app.use(express.static(buildPath));


// --- Auphonic API Proxy ---
const AUPHONIC_API_BASE = 'https://auphonic.com/api';
const { AUPHONIC_USERNAME, AUPHONIC_PASSWORD } = process.env;
const auphonicRouter = express.Router();

// Middleware to check for Auphonic credentials on all Auphonic-proxied routes
auphonicRouter.use((req, res, next) => {
    if (!AUPHONIC_USERNAME || !AUPHONIC_PASSWORD) {
        console.error('Auphonic API credentials are not configured on the server.');
        return res.status(503).json({ 
            error: 'Auphonic service is not configured.',
            details: 'The server is missing the required AUPHONIC_USERNAME and AUPHONIC_PASSWORD environment variables for authentication.'
        });
    }
    next();
});

const AUPHONIC_AUTH = 'Basic ' + Buffer.from(`${AUPHONIC_USERNAME}:${AUPHONIC_PASSWORD}`).toString('base64');


// 1. Create Production and Upload File
auphonicRouter.post('/productions', async (req, res) => {
    const form = formidable({ keepExtensions: true, maxFileSize: 500 * 1024 * 1024 }); // 500MB limit

    form.parse(req, async (err, fields, files) => {
        if (err) {
            return res.status(500).json({ error: 'Error parsing form data.', details: err.message });
        }

        const inputFile = files.input_file?.[0];
        if (!inputFile) {
            return res.status(400).json({ error: 'No input file uploaded.' });
        }

        try {
            const formData = new FormData();
            formData.append('action', 'new');
            formData.append('input_file', fs.createReadStream(inputFile.filepath), inputFile.originalFilename);

            const response = await fetch(`${AUPHONIC_API_BASE}/productions.json`, {
                method: 'POST',
                headers: {
                    'Authorization': AUPHONIC_AUTH,
                    ...formData.getHeaders(),
                },
                body: formData,
            });

            const responseData = await response.json();
            if (!response.ok) {
                return res.status(response.status).json({
                    error: `Auphonic Create Error: ${JSON.stringify(responseData)}`,
                });
            }
            
            fs.unlink(inputFile.filepath, (unlinkErr) => {
                if(unlinkErr) console.error("Error deleting temp file:", unlinkErr);
            });

            res.status(200).json({ uuid: responseData.data.uuid });

        } catch (error) {
            res.status(500).json({ error: 'Failed to create Auphonic production.', details: error.message });
        }
    });
});


// 2. Start Production
auphonicRouter.post('/productions/:uuid/start', async (req, res) => {
    const { uuid } = req.params;
    const { generateTranscript, auphonicProcessing } = req.body;

    const payload = {
        output_basename: `audiogram_${uuid.substring(0, 8)}`,
        output_files: [{ format: "wav", bitrate: "0" }],
        services: generateTranscript ? [{ identifier: "whisper", activate: true }] : [],
        algorithms: {
            leveler: auphonicProcessing.adaptiveLeveler,
            denoise: auphonicProcessing.noiseAndHumReduction,
            denoiseamount: auphonicProcessing.noiseReductionAmount === 0 ? "auto" : auphonicProcessing.noiseReductionAmount.toString(),
            hipfilter: auphonicProcessing.filtering,
            normloudness: true,
            loudnesstarget: auphonicProcessing.loudnessTarget.toString(),
        }
    };
    
    try {
        const response = await fetch(`${AUPHONIC_API_BASE}/production/${uuid}/start.json`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': AUPHONIC_AUTH },
            body: JSON.stringify(payload),
        });

        if (!response.ok) throw new Error(`Auphonic API returned ${response.status}`);
        res.status(200).json({ message: 'Production started' });

    } catch (error) {
        res.status(500).json({ error: 'Failed to start Auphonic production.', details: error.message });
    }
});


// 3. Get Production Status
auphonicRouter.get('/productions/:uuid', async (req, res) => {
    const { uuid } = req.params;
    try {
        const response = await fetch(`${AUPHONIC_API_BASE}/production/${uuid}.json`, {
            headers: { 'Authorization': AUPHONIC_AUTH }
        });
        if (!response.ok) throw new Error(`Auphonic API returned ${response.status}`);
        const data = await response.json();
        res.status(200).json(data);
    } catch (error) {
        res.status(500).json({ error: 'Failed to get production status.', details: error.message });
    }
});

// 4. Get Production Results (to get download URLs)
auphonicRouter.get('/productions/:uuid/results', async (req, res) => {
    const { uuid } = req.params;
    try {
        const response = await fetch(`${AUPHONIC_API_BASE}/production/${uuid}.json`, {
            headers: { 'Authorization': AUPHONIC_AUTH }
        });
        if (!response.ok) throw new Error(`Auphonic API returned ${response.status}`);
        const data = await response.json();
        res.status(200).json(data);
    } catch (error) {
        res.status(500).json({ error: 'Failed to get production results.', details: error.message });
    }
});

app.use('/api/auphonic', auphonicRouter);


// --- Fallback for client-side routing ---
app.get('*', (req, res) => {
  res.sendFile(path.join(buildPath, 'index.html'));
});


app.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
});