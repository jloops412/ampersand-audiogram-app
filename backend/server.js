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

// Serve the static frontend from the 'dist' directory
app.use(express.static(path.join(__dirname, '..', 'dist')));

// --- Auphonic API Configuration ---
const AUPHONIC_API_BASE = 'https://auphonic.com/api';
const USERNAME = process.env.AUPHONIC_USERNAME;
const PASSWORD = process.env.AUPHONIC_PASSWORD;

// --- Diagnostic Logging on Startup ---
console.log('--- Server Configuration ---');
if (USERNAME && USERNAME.length > 0) {
    console.log('✅ AUPHONIC_USERNAME is set.');
} else {
    console.log('❌ AUPHONIC_USERNAME is NOT SET or is empty.');
}
if (PASSWORD && PASSWORD.length > 0) {
    console.log('✅ AUPHONIC_PASSWORD is set.');
} else {
    console.log('❌ AUPHONIC_PASSWORD is NOT SET or is empty.');
}
console.log('--------------------------');


// Middleware to check for Auphonic credentials
const checkAuphonicCredentials = (req, res, next) => {
    if (!USERNAME || !PASSWORD) {
        return res.status(503).json({
            error: "Auphonic service is not configured.",
            details: "The server is missing the required AUPHONIC_USERNAME and AUPHONIC_PASSWORD environment variables for authentication."
        });
    }
    next();
};

const getAuthHeader = () => {
    return 'Basic ' + Buffer.from(USERNAME + ':' + PASSWORD).toString('base64');
};

// A list to keep track of temporary files for cleanup
let tempFilePaths = [];

// --- API Routes ---

// 1. Create Production (and upload files)
app.post('/api/auphonic/productions', checkAuphonicCredentials, async (req, res) => {
    const form = formidable({ keepExtensions: true, allowEmptyFiles: false });

    form.parse(req, async (err, fields, files) => {
        if (err) {
            console.error('Formidable parsing error:', err);
            return res.status(500).json({ error: 'Error parsing form data' });
        }
        
        try {
            const audioFile = files.input_file?.[0];
            const imageFile = files.image?.[0];
            const generateTranscript = fields.generateTranscript?.[0] === 'true';

            if (!audioFile) {
                return res.status(400).json({ error: 'Audio file (input_file) is required.' });
            }

            const auphonicForm = new FormData();
            const metadata = {
                title: audioFile.originalFilename || `Audiogram Production ${new Date().toISOString()}`,
                action: 'start', // Immediately start after upload
            };
            if (generateTranscript) {
                metadata.services = { wt: { "language": "en" } }; // Request whisper transcript in English
            }

            auphonicForm.append('metadata', JSON.stringify(metadata));
            auphonicForm.append('input_file', fs.createReadStream(audioFile.filepath), audioFile.originalFilename);
            if (imageFile) {
                auphonicForm.append('image', fs.createReadStream(imageFile.filepath), imageFile.originalFilename);
                tempFilePaths.push(imageFile.filepath);
            }
            tempFilePaths.push(audioFile.filepath);
            
            const response = await fetch(`${AUPHONIC_API_BASE}/productions.json`, {
                method: 'POST',
                headers: {
                    'Authorization': getAuthHeader(),
                    ...auphonicForm.getHeaders()
                },
                body: auphonicForm,
            });

            if (!response.ok) {
                const errorBody = await response.text();
                throw new Error(`Auphonic Create Error: ${errorBody}`);
            }

            const responseData = await response.json();
            res.status(200).json({ uuid: responseData.data.uuid });

        } catch (error) {
            console.error('Auphonic production creation failed:', error);
            res.status(500).json({ error: error.message });
        }
    });
});


// 2. Get Production Status
app.get('/api/auphonic/productions/:uuid', checkAuphonicCredentials, async (req, res) => {
    const { uuid } = req.params;
    try {
        const response = await fetch(`${AUPHONIC_API_BASE}/production/${uuid}.json`, {
            headers: { 'Authorization': getAuthHeader() }
        });
        if (!response.ok) {
            const errorBody = await response.text();
            throw new Error(`Failed to get status for production ${uuid}: ${errorBody}`);
        }
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Failed to fetch Auphonic production status' });
    }
});


// 3. Securely Download Production Results
app.get('/api/auphonic/download', checkAuphonicCredentials, async (req, res) => {
    const downloadUrl = req.query.url;
    if (!downloadUrl) {
        return res.status(400).send('Download URL is required.');
    }
    try {
        const response = await fetch(downloadUrl, {
            headers: { 'Authorization': getAuthHeader() }
        });
        if (!response.ok) {
            throw new Error(`Failed to download file from Auphonic: ${response.statusText}`);
        }
        // Stream the file back to the client
        res.setHeader('Content-Type', response.headers.get('Content-Type'));
        response.body.pipe(res);
    } catch (error) {
        console.error('Download proxy error:', error);
        res.status(500).send('Failed to download file.');
    }
});

// Catch-all to serve the index.html for any other route (for client-side routing)
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, '..', 'dist', 'index.html'));
});

// --- Server Startup ---
app.listen(PORT, () => {
    console.log(`🚀 Server is listening on port ${PORT}`);
});

// --- Graceful Shutdown & Cleanup ---
const cleanup = () => {
  console.log('Cleaning up temporary files...');
  tempFilePaths.forEach(filePath => {
    if (fs.existsSync(filePath)) {
      try {
        fs.unlinkSync(filePath);
        console.log(`Deleted temp file: ${filePath}`);
      } catch (err) {
        console.error(`Error deleting temp file ${filePath}:`, err);
      }
    }
  });
  process.exit();
};

process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);
