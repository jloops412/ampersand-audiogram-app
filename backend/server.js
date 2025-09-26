import express from 'express';
import cors from 'cors';
import fetch from 'node-fetch';
import { formidable } from 'formidable';
import FormData from 'form-data';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 8080;

// Middleware
app.use(cors());
app.use(express.json());

// Serve frontend static files
const frontendDistPath = path.join(__dirname, '..', 'dist');
app.use(express.static(frontendDistPath));

// --- Auphonic API Configuration ---
const AUPHONIC_API_BASE = 'https://auphonic.com/api';
const AUPHONIC_USERNAME = process.env.AUPHONIC_USERNAME;
const AUPHONIC_PASSWORD = process.env.AUPHONIC_PASSWORD;

// Diagnostic logging on startup
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
            error: "Auphonic service is not configured.",
            details: "The server is missing the required AUPHONIC_USERNAME and AUPHONIC_PASSWORD environment variables for authentication."
        });
    }
    next();
};

const getAuthHeader = () => `Basic ${Buffer.from(`${AUPHONIC_USERNAME}:${AUPHONIC_PASSWORD}`).toString('base64')}`;

// --- API Routes ---

/**
 * Creates a production, uploads files, and starts it.
 * This uses a robust two-step process to avoid API ambiguity.
 */
app.post('/api/auphonic/productions', checkAuphonicCredentials, async (req, res) => {
    const form = formidable({ keepExtensions: true });
    let tempFilePaths = [];

    try {
        form.parse(req, async (err, fields, files) => {
            if (err) {
                console.error('Form parsing error:', err);
                return res.status(400).json({ error: 'Failed to parse form data.' });
            }

            const { input_file, image } = files;
            const { generateTranscript } = fields;

            if (!input_file || !input_file[0]) {
                return res.status(400).json({ error: 'Audio file (input_file) is required.' });
            }
            
            const audioFilePath = input_file[0].filepath;
            tempFilePaths.push(audioFilePath);
            
            // --- Step 1: Create Production and Upload Files ---
            const createForm = new FormData();
            createForm.append('input_file', fs.createReadStream(audioFilePath));
            createForm.append('action', 'start'); // Start immediately
            
            if(generateTranscript && generateTranscript[0] === 'true') {
                createForm.append('services', JSON.stringify([{ "identifier": "whisper", "parameters": { "language": "auto" } }]));
            }

            if (image && image[0]) {
                const imageFilePath = image[0].filepath;
                tempFilePaths.push(imageFilePath);
                createForm.append('image', fs.createReadStream(imageFilePath));
            }
            
            const createResponse = await fetch(`${AUPHONIC_API_BASE}/productions.json`, {
                method: 'POST',
                headers: { ...createForm.getHeaders(), 'Authorization': getAuthHeader() },
                body: createForm,
            });

            const createData = await createResponse.json();

            if (!createResponse.ok) {
                console.error('Auphonic Create Error:', createData);
                return res.status(500).json({ error: `Auphonic Create Error: ${JSON.stringify(createData)}` });
            }

            res.status(200).json({ uuid: createData.data.uuid });
        });
    } catch (error) {
        console.error('Error creating Auphonic production:', error);
        res.status(500).json({ error: 'Internal server error during production creation.' });
    } finally {
        // Asynchronous cleanup without holding up the response
        setTimeout(() => {
            tempFilePaths.forEach(p => fs.unlink(p, () => {}));
        }, 10000); // 10s delay
    }
});


/**
 * Gets the status of a specific production.
 */
app.get('/api/auphonic/productions/:uuid', checkAuphonicCredentials, async (req, res) => {
    const { uuid } = req.params;
    try {
        const response = await fetch(`${AUPHONIC_API_BASE}/production/${uuid}.json`, {
            headers: { 'Authorization': getAuthHeader() }
        });
        const data = await response.json();
        if (!response.ok) {
            return res.status(response.status).json({ error: 'Failed to fetch production status from Auphonic.' });
        }
        res.status(200).json(data);
    } catch (error) {
        console.error(`Error fetching status for UUID ${uuid}:`, error);
        res.status(500).json({ error: 'Internal server error.' });
    }
});

/**
 * Securely proxies a download from Auphonic's servers.
 */
app.get('/api/auphonic/download', checkAuphonicCredentials, async (req, res) => {
    const { url } = req.query;
    if (!url) {
        return res.status(400).send('Download URL is required.');
    }
    try {
        const response = await fetch(url, {
            headers: { 'Authorization': getAuthHeader() }
        });
        if (!response.ok) {
            return res.status(response.status).send('Failed to fetch file from Auphonic.');
        }
        res.setHeader('Content-Type', response.headers.get('content-type') || 'application/octet-stream');
        response.body.pipe(res);
    } catch (error) {
        console.error('Error proxying download:', error);
        res.status(500).send('Internal server error while downloading file.');
    }
});


// Fallback to serving index.html for any other request (for client-side routing)
app.get('*', (req, res) => {
  res.sendFile(path.join(frontendDistPath, 'index.html'));
});

app.listen(PORT, () => {
  console.log(`🚀 Server is listening on port ${PORT}`);
});
