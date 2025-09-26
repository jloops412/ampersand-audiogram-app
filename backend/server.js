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

// Get the directory name of the current module
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Serve static files from the React app build directory
const frontendDistPath = path.join(__dirname, '..', 'dist');
app.use(express.static(frontendDistPath));

// --- Auphonic Configuration & Auth Check ---
const AUPHONIC_API_BASE = 'https://auphonic.com/api';
const { AUPHONIC_USERNAME, AUPHONIC_PASSWORD } = process.env;

// Middleware to check if Auphonic credentials are configured on the server
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

// Create a production and upload the file (robust two-step process)
app.post('/api/auphonic/productions', checkAuphonicConfig, async (req, res) => {
  try {
    // 1. Handle file upload from the client using formidable
    const form = formidable({ 
      maxFileSize: 500 * 1024 * 1024, // 500 MB limit
      uploadDir: '/tmp', // Use a temporary directory
    });

    const [fields, files] = await form.parse(req);
    const inputFile = files.input_file?.[0];

    if (!inputFile) {
      return res.status(400).json({ error: 'No input file was uploaded.' });
    }

    // 2. Create the production on Auphonic (first step)
    const createResponse = await fetch(`${AUPHONIC_API_BASE}/productions.json`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Basic ' + Buffer.from(`${AUPHONIC_USERNAME}:${AUPHONIC_PASSWORD}`).toString('base64')
      },
      body: JSON.stringify({ title: inputFile.originalFilename || 'Audiogram Production' })
    });
    
    if (!createResponse.ok) {
        const errorData = await createResponse.json();
        throw new Error(`Auphonic Create Error: ${JSON.stringify(errorData)}`);
    }

    const { data: { uuid } } = await createResponse.json();

    // 3. Upload the file to the created production (second step)
    const formData = new FormData();
    formData.append('input_file', fs.createReadStream(inputFile.filepath), inputFile.originalFilename);

    const uploadResponse = await fetch(`${AUPHONIC_API_BASE}/production/${uuid}/upload.json`, {
      method: 'POST',
      headers: {
        ...formData.getHeaders(),
        'Authorization': 'Basic ' + Buffer.from(`${AUPHONIC_USERNAME}:${AUPHONIC_PASSWORD}`).toString('base64')
      },
      body: formData
    });
    
    // Clean up the temporary file
    fs.unlinkSync(inputFile.filepath);

    if (!uploadResponse.ok) {
        const errorData = await uploadResponse.json();
        throw new Error(`Auphonic Upload Error: ${JSON.stringify(errorData)}`);
    }

    res.status(200).json({ uuid });
    
  } catch (error) {
    console.error('Error in /api/auphonic/productions:', error);
    res.status(500).json({ error: error.message });
  }
});


// Get production status
app.get('/api/auphonic/productions/:uuid', checkAuphonicConfig, async (req, res) => {
    try {
        const { uuid } = req.params;
        const response = await fetch(`${AUPHONIC_API_BASE}/production/${uuid}.json`, {
             headers: { 'Authorization': 'Basic ' + Buffer.from(`${AUPHONIC_USERNAME}:${AUPHONIC_PASSWORD}`).toString('base64') }
        });
        const data = await response.json();
        res.status(response.status).json(data);
    } catch (error) {
        res.status(500).json({ error: 'Failed to get production status.' });
    }
});

// Start a production
app.post('/api/auphonic/productions/:uuid/start', checkAuphonicConfig, async (req, res) => {
  try {
    const { uuid } = req.params;
    const { generateTranscript, auphonicProcessing } = req.body;
    
    const payload = {
      action: 'start',
      output_files: [{ format: 'wav' }],
      algorithms: {
        adaptive_leveler: auphonicProcessing.adaptiveLeveler,
        noise_and_hum_reduction: auphonicProcessing.noiseAndHumReduction,
        noise_reduction_amount: auphonicProcessing.noiseReductionAmount === 0 ? undefined : auphonicProcessing.noiseReductionAmount,
        hip_filter: auphonicProcessing.filtering,
        loudness_normalization: true,
        loudness_target: auphonicProcessing.loudnessTarget,
      }
    };

    if (generateTranscript) {
      payload.services = [{ identifier: 'whisper' }];
    }
    
    const response = await fetch(`${AUPHONIC_API_BASE}/production/${uuid}.json`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Basic ' + Buffer.from(`${AUPHONIC_USERNAME}:${AUPHONIC_PASSWORD}`).toString('base64')
      },
      body: JSON.stringify(payload)
    });
    
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Auphonic Start Error: ${JSON.stringify(errorData)}`);
    }

    const data = await response.json();
    res.status(200).json(data);

  } catch (error) {
    console.error('Error starting production:', error.message);
    res.status(500).json({ error: 'Failed to start Auphonic production.' });
  }
});


// Get production results
app.get('/api/auphonic/productions/:uuid/results', checkAuphonicConfig, async (req, res) => {
    try {
        const { uuid } = req.params;
        // The API endpoint for results is just the main production endpoint after it's done.
        const response = await fetch(`${AUPHONIC_API_BASE}/production/${uuid}.json`, {
             headers: { 'Authorization': 'Basic ' + Buffer.from(`${AUPHONIC_USERNAME}:${AUPHONIC_PASSWORD}`).toString('base64') }
        });
        const data = await response.json();
        res.status(response.status).json(data);
    } catch (error) {
        res.status(500).json({ error: 'Failed to get production results.' });
    }
});


// --- Fallback for client-side routing ---
// This should be the last route
app.get('*', (req, res) => {
  res.sendFile(path.join(frontendDistPath, 'index.html'));
});


app.listen(PORT, () => {
  console.log(`✅ Server is running and listening on port ${PORT}`);
  console.log(`Serving frontend from: ${frontendDistPath}`);
});
