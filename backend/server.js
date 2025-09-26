import express from 'express';
import cors from 'cors';
import fetch from 'node-fetch';
import { formidable } from 'formidable';
import FormData from 'form-data';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const app = express();
const PORT = process.env.PORT || 8080;

// --- Middleware ---
app.use(cors());
app.use(express.json());

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Serve static files from the React app build directory
app.use(express.static(path.join(__dirname, '..', 'dist')));

// --- Auphonic API Configuration ---
const AUPHONIC_API_BASE = 'https://auphonic.com/api';
const AUPHONIC_USERNAME = process.env.AUPHONIC_USERNAME;
const AUPHONIC_PASSWORD = process.env.AUPHONIC_PASSWORD;

// --- Diagnostic Logging ---
console.log('--- Server Configuration ---');
if (AUPHONIC_USERNAME && AUPHONIC_USERNAME.length > 0) {
    console.log('✅ AUPHONIC_USERNAME is SET.');
} else {
    console.log('❌ AUPHONIC_USERNAME is NOT SET or is empty.');
}
if (AUPHONIC_PASSWORD && AUPHONIC_PASSWORD.length > 0) {
    console.log('✅ AUPHONIC_PASSWORD is SET.');
} else {
    console.log('❌ AUPHONIC_PASSWORD is NOT SET or is empty.');
}
console.log('--------------------------');


// Middleware to check for Auphonic credentials
const checkAuphonicCredentials = (req, res, next) => {
    if (!AUPHONIC_USERNAME || !AUPHONIC_PASSWORD) {
        return res.status(503).json({
            error: 'Auphonic service is not configured.',
            details: 'The server is missing the required AUPHONIC_USERNAME and AUPHONIC_PASSWORD environment variables for authentication.'
        });
    }
    next();
};

const getAuthHeader = () => {
    const credentials = Buffer.from(`${AUPHONIC_USERNAME}:${AUPHONIC_PASSWORD}`).toString('base64');
    return `Basic ${credentials}`;
};

// --- API Routes ---

// 1. Create a production, get a UUID, then upload the file to it.
app.post('/api/auphonic/productions', checkAuphonicCredentials, async (req, res) => {
    const form = formidable({ 
        uploadDir: '/tmp', // Use a temporary directory for uploads
        keepExtensions: true 
    });

    form.parse(req, async (err, fields, files) => {
        if (err) {
            console.error('Formidable parsing error:', err);
            return res.status(500).json({ error: 'Error parsing form data' });
        }

        const inputFile = files.input_file?.[0];
        if (!inputFile) {
            return res.status(400).json({ error: 'No input file provided' });
        }
        
        const audioFileName = inputFile.originalFilename || 'audio.tmp';

        try {
            // Step 1: Create the production with metadata
            const createResponse = await fetch(`${AUPHONIC_API_BASE}/productions.json`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': getAuthHeader()
                },
                body: JSON.stringify({ metadata: { title: `Audiogram - ${audioFileName}` } }),
            });

            if (!createResponse.ok) {
                const errorData = await createResponse.json();
                console.error('Auphonic Create Error:', errorData);
                return res.status(createResponse.status).json({ error: `Auphonic Create Error: ${JSON.stringify(errorData)}` });
            }

            const { data: { uuid } } = await createResponse.json();

            // Step 2: Upload the file to the new production
            const formUpload = new FormData();
            formUpload.append('input_file', fs.createReadStream(inputFile.filepath), audioFileName);
            
            const uploadResponse = await fetch(`${AUPHONIC_API_BASE}/production/${uuid}/upload.json`, {
                method: 'POST',
                headers: {
                    ...formUpload.getHeaders(),
                    'Authorization': getAuthHeader()
                },
                body: formUpload,
            });

            if (!uploadResponse.ok) {
                const errorData = await uploadResponse.text();
                console.error('Auphonic Upload Error:', errorData);
                return res.status(uploadResponse.status).json({ error: `Auphonic Upload Error: ${errorData}` });
            }

            // Cleanup the temporary file
            fs.unlink(inputFile.filepath, (unlinkErr) => {
                if(unlinkErr) console.error("Error deleting temp file:", unlinkErr);
            });

            res.status(200).json({ uuid });

        } catch (error) {
            console.error('Error during Auphonic creation/upload:', error);
            res.status(500).json({ error: error.message });
            // Cleanup in case of error
            fs.unlink(inputFile.filepath, (unlinkErr) => {
                if(unlinkErr) console.error("Error deleting temp file on failure:", unlinkErr);
            });
        }
    });
});


// 2. Start a production
app.post('/api/auphonic/productions/:uuid/start', checkAuphonicCredentials, async (req, res) => {
    const { uuid } = req.params;
    const { generateTranscript, auphonicProcessing } = req.body;

    const payload = {
        action: 'start',
        ...(generateTranscript && { services: { whisper: { language: 'auto' } } }),
        output_files: [ { format: 'wav' } ], // Request a high-quality audio output
        algorithms: {
            leveler: auphonicProcessing.adaptiveLeveler,
            denoise: auphonicProcessing.noiseAndHumReduction,
            denoiseamount: auphonicProcessing.noiseReductionAmount === 0 ? 'auto' : auphonicProcessing.noiseReductionAmount,
            hipfilter: auphonicProcessing.filtering,
            normloudness: true,
            loudnesstarget: auphonicProcessing.loudnessTarget,
        }
    };
    
    try {
        const response = await fetch(`${AUPHONIC_API_BASE}/production/${uuid}.json`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': getAuthHeader() },
            body: JSON.stringify(payload),
        });
        if (!response.ok) throw new Error('Failed to start Auphonic production');
        res.status(200).json({ message: 'Production started' });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// 3. Get production status
app.get('/api/auphonic/productions/:uuid', checkAuphonicCredentials, async (req, res) => {
    const { uuid } = req.params;
    try {
        const response = await fetch(`${AUPHONIC_API_BASE}/production/${uuid}.json`, {
            headers: { 'Authorization': getAuthHeader() }
        });
        if (!response.ok) throw new Error('Failed to get production status');
        const data = await response.json();
        res.status(200).json(data);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// 4. Get production results
app.get('/api/auphonic/productions/:uuid/results', checkAuphonicCredentials, async (req, res) => {
    const { uuid } = req.params;
    try {
        const response = await fetch(`${AUPHONIC_API_BASE}/production/${uuid}.json`, {
            headers: { 'Authorization': getAuthHeader() }
        });
        if (!response.ok) throw new Error('Failed to get production results');
        const data = await response.json();
        res.status(200).json(data);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});


// --- Serve React App ---
// All other GET requests not handled by the API will be served the React app.
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'dist', 'index.html'));
});

// --- Start Server ---
app.listen(PORT, () => {
  console.log(`🚀 Server is listening on port ${PORT}`);
});
