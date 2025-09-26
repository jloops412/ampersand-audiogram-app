// backend/server.js
import express from 'express';
import cors from 'cors';
import fetch from 'node-fetch';
import formidable from 'formidable';
import FormData from 'form-data';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const app = express();
const PORT = process.env.PORT || 8080;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// --- Middleware ---
app.use(cors());
app.use(express.json());

// Serve the frontend
app.use(express.static(path.join(__dirname, '..', 'dist')));

// --- Auphonic API Configuration ---
const AUPHONIC_API_BASE = 'https://auphonic.com/api';
const { AUPHONIC_USERNAME, AUPHONIC_PASSWORD } = process.env;

const checkAuphonicCredentials = (req, res, next) => {
    if (!AUPHONIC_USERNAME || !AUPHONIC_PASSWORD) {
        console.error('Auphonic credentials are not set on the server.');
        return res.status(503).json({
            error: 'Auphonic service is not configured.',
            details: 'The server is missing the required AUPHONIC_USERNAME and AUPHONIC_PASSWORD environment variables for authentication.'
        });
    }
    next();
};

const getAuthHeader = () => {
    return 'Basic ' + Buffer.from(`${AUPHONIC_USERNAME}:${AUPHONIC_PASSWORD}`).toString('base64');
};

// --- API Routes ---

// 1. Create a Production (and upload files)
app.post('/api/auphonic/productions', checkAuphonicCredentials, async (req, res) => {
    // Use a simpler formidable setup, letting it use the OS temp directory
    const form = formidable({});

    form.parse(req, async (err, fields, files) => {
        if (err) {
            console.error('Error parsing form data:', err);
            return res.status(500).json({ error: 'Failed to process uploaded files.' });
        }

        const audioFile = files.audio?.[0];
        const coverImageFile = files.coverImage?.[0];

        if (!audioFile) {
            return res.status(400).json({ error: 'Audio file is required.' });
        }

        let tempFilePaths = [];

        try {
            const formData = new FormData();
            
            // Add user's specific preset
            formData.append('preset', 'LcXbNksM7Li9oBpWAt5o4H');

            // Required: Add audio file
            formData.append('input_file', fs.createReadStream(audioFile.filepath));
            tempFilePaths.push(audioFile.filepath);
            
            // Optional: Add cover image
            if (coverImageFile) {
                formData.append('image', fs.createReadStream(coverImageFile.filepath));
                tempFilePaths.push(coverImageFile.filepath);
            }

            // Optional: Add metadata (title from filename)
            formData.append('metadata[title]', path.parse(audioFile.originalFilename || 'audiogram').name);
            
            const auphonicResponse = await fetch(`${AUPHONIC_API_BASE}/productions.json`, {
                method: 'POST',
                headers: {
                    ...formData.getHeaders(),
                    'Authorization': getAuthHeader()
                },
                body: formData,
            });

            const responseData = await auphonicResponse.json();

            if (!auphonicResponse.ok) {
                console.error('Auphonic Create Error:', responseData);
                return res.status(500).json({ error: 'Auphonic Create Error', details: responseData });
            }

            // Return the new production data (contains UUID)
            res.status(201).json(responseData.data);

        } catch (error) {
            console.error('Error creating Auphonic production:', error);
            res.status(500).json({ error: 'Internal server error during production creation.' });
        } finally {
             // Cleanup uploaded temp files
            tempFilePaths.forEach(filePath => fs.unlink(filePath, () => {}));
        }
    });
});

// 2. Start a Production
app.post('/api/auphonic/productions/:uuid/start', checkAuphonicCredentials, async (req, res) => {
    const { uuid } = req.params;
    const { generateTranscript } = req.body;

    try {
        const body = {};
        if (generateTranscript) {
           // Enables transcription and speech recognition
           body.webhook = "https://auphonic.com/api/webhook/end-and-start-speech-recognition/json/";
        }

        const auphonicResponse = await fetch(`${AUPHONIC_API_BASE}/production/${uuid}/start.json`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': getAuthHeader()
            },
            // Sending an empty body is fine, it will use the preset's settings
            body: Object.keys(body).length > 0 ? JSON.stringify(body) : undefined,
        });

        if (!auphonicResponse.ok) {
            const errorData = await auphonicResponse.json();
            console.error('Auphonic Start Error:', errorData);
            return res.status(auphonicResponse.status).json({ error: 'Failed to start Auphonic production.', details: errorData });
        }
        
        res.status(200).json({ message: 'Production started successfully.' });

    } catch (error) {
        console.error('Error starting production:', error);
        res.status(500).json({ error: 'Internal server error.' });
    }
});


// 3. Get Production Status
app.get('/api/auphonic/productions/:uuid', checkAuphonicCredentials, async (req, res) => {
    const { uuid } = req.params;
    try {
        const auphonicResponse = await fetch(`${AUPHONIC_API_BASE}/production/${uuid}.json`, {
            headers: { 'Authorization': getAuthHeader() }
        });
        const responseData = await auphonicResponse.json();

        if (!auphonicResponse.ok) {
            return res.status(auphonicResponse.status).json({ error: 'Failed to get production status.', details: responseData });
        }
        res.status(200).json(responseData.data);
    } catch (error) {
        console.error('Error fetching production status:', error);
        res.status(500).json({ error: 'Internal server error.' });
    }
});

// 4. Securely Download Production Results
app.get('/api/auphonic/download', checkAuphonicCredentials, async (req, res) => {
    const { url } = req.query;
    if (!url) {
        return res.status(400).send('Download URL is required.');
    }

    try {
        const auphonicResponse = await fetch(url, {
            headers: { 'Authorization': getAuthHeader() }
        });

        if (!auphonicResponse.ok) {
            return res.status(auphonicResponse.status).send('Failed to download file from Auphonic.');
        }

        // Stream the file back to the client
        res.setHeader('Content-Type', auphonicResponse.headers.get('Content-Type') || 'application/octet-stream');
        auphonicResponse.body.pipe(res);

    } catch (error) {
        console.error('Error proxying download:', error);
        res.status(500).send('Internal server error during download.');
    }
});


// --- Server Initialization ---
app.listen(PORT, () => {
    console.log(`✅ Server is running on port ${PORT}`);
    if (AUPHONIC_USERNAME && AUPHONIC_PASSWORD) {
        console.log('✅ Auphonic credentials are configured.');
    } else {
        console.warn('⚠️ AUPHONIC_USERNAME or AUPHONIC_PASSWORD is NOT SET. Auphonic features will not work.');
    }
});