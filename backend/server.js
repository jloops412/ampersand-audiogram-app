import express from 'express';
import fetch from 'node-fetch';
import { formidable } from 'formidable';
import { createReadStream } from 'fs';
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

// 1. Create Production & Upload File
app.post('/api/auphonic/productions', async (req, res) => {
    const form = formidable({});
    form.parse(req, async (err, fields, files) => {
        if (err || !files.input_file) {
            console.error('Form parsing error or file missing:', err);
            return res.status(500).send('Form parsing error or input_file missing');
        }
        
        const inputFile = files.input_file[0];
        const fileStream = createReadStream(inputFile.filepath);
        
        try {
            const createRes = await fetch(`${AUPHONIC_API_BASE}/productions.json`, {
                method: 'POST',
                headers: { 'Authorization': AUTH_HEADER, 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });
            if (!createRes.ok) throw new Error(`Auphonic Create Error: ${await createRes.text()}`);
            const { data: { uuid } } = await createRes.json();
            
            const uploadRes = await fetch(`${AUPHONIC_API_BASE}/production/${uuid}/upload.json`, {
                method: 'POST',
                headers: { 'Authorization': AUTH_HEADER },
                body: fileStream
            });
            if (!uploadRes.ok) throw new Error(`Auphonic Upload Error: ${await uploadRes.text()}`);
            
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
    const { preset, generateTranscript } = req.body;
    
    const payload = { preset };
    if (generateTranscript) {
        payload.services = { whisper: true };
        payload.output_files = [{ format: 'vtt' }];
    }

    try {
        const apiRes = await fetch(`${AUPHONIC_API_BASE}/production/${uuid}/start.json`, {
            method: 'POST',
            headers: { 'Authorization': AUTH_HEADER, 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!apiRes.ok) throw new Error(`Auphonic Start Error: ${await apiRes.text()}`);
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
