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

// --- Middlewares ---
app.use(cors());
app.use(express.json());

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const frontendDistPath = path.join(__dirname, '..', 'dist');
app.use(express.static(frontendDistPath));

// --- Auphonic Configuration & Auth Check ---
const AUPHONIC_API_BASE = 'https://auphonic.com/api';
const { AUPHONIC_USERNAME, AUPHONIC_PASSWORD } = process.env;

const checkAuphonicConfig = (req, res, next) => {
  if (!AUPHONIC_USERNAME || !AUPHONIC_PASSWORD) {
    console.error('Auphonic credentials are not set on the server.');
    return res.status(503).json({
      error: "Auphonic service is not configured.",
      details: "The server is missing the required AUPHONIC_USERNAME and AUPHONIC_PASSWORD environment variables for authentication."
    });
  }
  next();
};

const getAuthHeader = () => 'Basic ' + Buffer.from(`${AUPHONIC_USERNAME}:${AUPHONIC_PASSWORD}`).toString('base64');

// --- Diagnostic Logging ---
console.log('Server starting up...');
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

// --- API Routes ---

// Create a production, upload files, and start it (robust two-step flow)
app.post('/api/auphonic/productions', checkAuphonicConfig, async (req, res) => {
  let tempFilePaths: string[] = [];
  try {
    const form = formidable({ 
      maxFileSize: 500 * 1024 * 1024,
      uploadDir: '/tmp',
    });

    const [fields, files] = await form.parse(req);
    const inputFile = files.input_file?.[0];
    const coverImageFile = files.image?.[0];
    const generateTranscript = fields.generateTranscript?.[0] === 'true';

    if (!inputFile) {
      return res.status(400).json({ error: 'No input file was uploaded.' });
    }
    tempFilePaths.push(inputFile.filepath);
    if(coverImageFile) tempFilePaths.push(coverImageFile.filepath);

    // --- Step 1: Create Production and Upload Files ---
    const createFormData = new FormData();
    createFormData.append('input_file', fs.createReadStream(inputFile.filepath), inputFile.originalFilename);
    if (coverImageFile) {
      createFormData.append('image', fs.createReadStream(coverImageFile.filepath), coverImageFile.originalFilename);
    }
    
    const createMetadata = {
        title: inputFile.originalFilename || 'Audiogram Production',
        output_files: [{ format: 'wav' }]
    };
    createFormData.append('metadata', JSON.stringify(createMetadata));

    const createResponse = await fetch(`${AUPHONIC_API_BASE}/productions.json`, {
      method: 'POST',
      headers: {
        ...createFormData.getHeaders(),
        'Authorization': getAuthHeader()
      },
      body: createFormData
    });

    if (!createResponse.ok) {
        const errorData = await createResponse.json();
        throw new Error(`Auphonic Create Error: ${JSON.stringify(errorData)}`);
    }
    const { data: { uuid } } = await createResponse.json();

    // --- Step 2: Start the Production ---
    const startMetadata: { services?: { identifier: string }[] } = {};
    if (generateTranscript) {
        startMetadata.services = [{ identifier: 'whisper' }];
    }

    const startResponse = await fetch(`${AUPHONIC_API_BASE}/production/${uuid}/start.json`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': getAuthHeader()
        },
        body: Object.keys(startMetadata).length > 0 ? JSON.stringify(startMetadata) : undefined
    });

    if (!startResponse.ok) {
        const errorData = await startResponse.json();
        throw new Error(`Auphonic Start Error: ${JSON.stringify(errorData)}`);
    }

    res.status(200).json({ uuid });
    
  } catch (error) {
    console.error('Error in /api/auphonic/productions:', error);
    res.status(500).json({ error: error.message });
  } finally {
      // Clean up temporary files
      tempFilePaths.forEach(p => fs.unlink(p, (err) => {
          if (err) console.error(`Failed to delete temp file: ${p}`, err);
      }));
  }
});

// Get production status
app.get('/api/auphonic/productions/:uuid', checkAuphonicConfig, async (req, res) => {
    try {
        const { uuid } = req.params;
        const response = await fetch(`${AUPHONIC_API_BASE}/production/${uuid}.json`, {
             headers: { 'Authorization': getAuthHeader() }
        });
        const data = await response.json();
        res.status(response.status).json(data);
    } catch (error) {
        res.status(500).json({ error: 'Failed to get production status.' });
    }
});

// Secure Download Proxy
app.get('/api/auphonic/download', checkAuphonicConfig, async (req, res) => {
    try {
        const { url } = req.query;
        if (!url || typeof url !== 'string') {
            return res.status(400).json({ error: 'A valid download URL must be provided.' });
        }

        // Fetch the file from Auphonic's secure URL using server credentials
        const response = await fetch(url, {
            headers: { 'Authorization': getAuthHeader() }
        });

        if (!response.ok) {
            throw new Error(`Failed to download file from Auphonic: ${response.statusText}`);
        }

        // Stream the file back to the client
        res.setHeader('Content-Type', response.headers.get('Content-Type') || 'application/octet-stream');
        res.setHeader('Content-Disposition', response.headers.get('Content-Disposition') || 'attachment');
        response.body.pipe(res);

    } catch (error) {
        console.error('Download proxy error:', error);
        res.status(500).json({ error: 'Failed to download file.' });
    }
});

// --- Fallback for client-side routing ---
app.get('*', (req, res) => {
  res.sendFile(path.join(frontendDistPath, 'index.html'));
});

app.listen(PORT, () => {
  console.log(`✅ Server is running and listening on port ${PORT}`);
  console.log(`Serving frontend from: ${frontendDistPath}`);
});