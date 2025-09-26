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

const AUPHONIC_API_BASE = 'https://auphonic.com/api';

app.use(cors());
app.use(express.json());

// Serve static files from the React app
app.use(express.static(path.join(__dirname, '../dist')));

// Middleware to check for Auphonic credentials
const checkAuphonicCredentials = (req, res, next) => {
  const username = process.env.AUPHONIC_USERNAME;
  const password = process.env.AUPHONIC_PASSWORD;

  if (!username || !password) {
    console.error('Auphonic credentials are not set on the server.');
    return res.status(503).json({
      error: 'Auphonic service is not configured.',
      details: 'The server is missing the required AUPHONIC_USERNAME and AUPHONIC_PASSWORD environment variables for authentication.'
    });
  }
  
  const auth = 'Basic ' + Buffer.from(username + ":" + password).toString('base64');
  req.auphonicAuth = auth;
  next();
};

app.post('/api/auphonic/productions', checkAuphonicCredentials, async (req, res) => {
    const form = formidable({
        uploadDir: path.join(__dirname, 'uploads'),
        keepExtensions: true,
        maxFileSize: 500 * 1024 * 1024, // 500 MB
    });

    form.parse(req, async (err, fields, files) => {
        if (err) {
            console.error('Error parsing form data:', err);
            return res.status(500).json({ error: 'Error processing file upload.' });
        }

        const audioFile = files.audioFile?.[0];
        const imageFile = files.coverImageFile?.[0];
        const title = fields.title?.[0] || 'Audiogram Production';

        if (!audioFile) {
            return res.status(400).json({ error: 'No audio file provided.' });
        }

        try {
            const formData = new FormData();
            formData.append('input_file', fs.createReadStream(audioFile.filepath));
            formData.append('action', 'start');
            formData.append('title', title);
            
            if (imageFile) {
                formData.append('image', fs.createReadStream(imageFile.filepath));
            }

            const auphonicRes = await fetch(`${AUPHONIC_API_BASE}/productions.json`, {
                method: 'POST',
                headers: {
                    ...formData.getHeaders(),
                    'Authorization': req.auphonicAuth,
                },
                body: formData,
            });

            const auphonicData = await auphonicRes.json();
            
            if (!auphonicRes.ok) {
                console.error('Auphonic Create Error:', auphonicData);
                return res.status(auphonicRes.status).json({ error: 'Auphonic Create Error', details: auphonicData });
            }

            res.status(200).json(auphonicData.data);
        } catch (error) {
            console.error('Error creating Auphonic production:', error);
            res.status(500).json({ error: 'Internal server error during production creation.' });
        } finally {
            // Cleanup uploaded files
            if (audioFile) fs.unlink(audioFile.filepath, () => {});
            if (imageFile) fs.unlink(imageFile.filepath, () => {});
        }
    });
});


app.get('/api/auphonic/productions/:uuid', checkAuphonicCredentials, async (req, res) => {
    const { uuid } = req.params;
    try {
        const response = await fetch(`${AUPHONIC_API_BASE}/production/${uuid}.json`, {
            headers: { 'Authorization': req.auphonicAuth }
        });
        const data = await response.json();
        if (!response.ok) {
            return res.status(response.status).json({ error: 'Failed to get production status.', details: data });
        }
        res.json(data.data);
    } catch (error) {
        console.error('Error fetching production status:', error);
        res.status(500).json({ error: 'Internal server error.' });
    }
});

app.get('/api/auphonic/productions/:uuid/download', checkAuphonicCredentials, async (req, res) => {
    const { uuid } = req.params;
    const { type } = req.query; // 'audio' or 'transcript'

    try {
        const prodDetailsRes = await fetch(`${AUPHONIC_API_BASE}/production/${uuid}.json`, {
            headers: { 'Authorization': req.auphonicAuth }
        });
        const prodDetails = await prodDetailsRes.json();

        if (!prodDetailsRes.ok) {
            return res.status(404).json({ error: 'Production details not found.' });
        }

        let downloadUrl;
        if (type === 'transcript') {
            const transcript = prodDetails.data.results.find(r => r.result_content_type.startsWith('text/plain'));
            downloadUrl = transcript?.download_url;
        } else { // audio
            const audio = prodDetails.data.results.find(r => r.result_content_type.startsWith('audio/'));
            downloadUrl = audio?.download_url;
        }

        if (!downloadUrl) {
            return res.status(404).json({ error: `Could not find ${type} result for this production.` });
        }

        const fileRes = await fetch(downloadUrl, {
             headers: { 'Authorization': req.auphonicAuth }
        });

        if (!fileRes.ok) {
            return res.status(fileRes.status).send('Failed to download file from Auphonic.');
        }

        res.setHeader('Content-Type', fileRes.headers.get('Content-Type') || 'application/octet-stream');
        fileRes.body.pipe(res);

    } catch (error) {
        console.error(`Error downloading ${type} file:`, error);
        res.status(500).json({ error: 'Internal server error during file download.' });
    }
});


// The "catchall" handler: for any request that doesn't
// match one above, send back React's index.html file.
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../dist/index.html'));
});

app.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
  // Diagnostic logging for environment variables
  if (process.env.AUPHONIC_USERNAME) {
    console.log('✅ AUPHONIC_USERNAME is SET.');
  } else {
    console.log('❌ AUPHONIC_USERNAME is NOT SET or is empty.');
  }
  if (process.env.AUPHONIC_PASSWORD) {
    console.log('✅ AUPHONIC_PASSWORD is SET.');
  } else {
    console.log('❌ AUPHONIC_PASSWORD is NOT SET or is empty.');
  }
});
