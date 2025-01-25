require('dotenv').config({ path: '/app/.env' }); // Load .env file from the mounted path
const express = require('express');
const cors = require('cors');
const { Storage } = require('@google-cloud/storage');
const path = require('path');

const app = express();
const port = 5000;

// Read the SERVER_ADDRESS from environment variables
const serverAddress = process.env.SERVER_ADDRESS || 'localhost';

// Configure CORS to allow requests from the SERVER_ADDRESS
app.use(
  cors()
);

// GCP Storage Client
const storage = new Storage({
  keyFilename: '/secrets/key-file.json', // Path to the mounted service account key file
});

const bucketName = 'state-sdtd-1'; // Replace with your GCP bucket name

// Route to fetch the latest image/GIF from the GCP bucket
app.get('/api/image', async (req, res) => {
  try {
    // List files in the bucket
    const [files] = await storage.bucket(bucketName).getFiles();

    if (!files.length) {
      return res.status(404).send('No files found in the bucket.');
    }

    // Sort files by creation time (newest first)
    files.sort((a, b) => new Date(b.metadata.timeCreated) - new Date(a.metadata.timeCreated));

    // Get the latest file
    const latestFile = files[0];
    const file = storage.bucket(bucketName).file(latestFile.name);

    // Fetch file metadata to determine content type
    const [metadata] = await file.getMetadata();
    const contentType = metadata.contentType || 'application/octet-stream';

    // Set appropriate headers
    res.setHeader('Content-Type', contentType);
    res.setHeader('Content-Disposition', `inline; filename="${path.basename(latestFile.name)}"`);

    // Create a read stream and pipe it to the response
    const readStream = file.createReadStream();

    // Handle stream errors
    readStream.on('error', (err) => {
      console.error('Error reading file from GCP bucket:', err);
      res.status(500).send('Internal Server Error');
    });

    // Pipe the read stream to the response
    readStream.pipe(res);
  } catch (err) {
    console.error('Error fetching image from GCP bucket:', err);
    res.status(500).send('Internal Server Error');
  }
});

app.listen(port, '0.0.0.0', () => {
    console.log(`Backend server listening on http://0.0.0.0:${port}`);
  });
