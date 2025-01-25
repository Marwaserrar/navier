const express = require('express');
const cors = require('cors');
const { Storage } = require('@google-cloud/storage');
const path = require('path');

const app = express();
const port = 5000;

// Middleware
app.use(cors());

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

    // Sort files by creation time (newest first)
    files.sort((a, b) => b.metadata.timeCreated - a.metadata.timeCreated);

    // Get the latest file
    const latestFile = files[0];

    if (!latestFile) {
      return res.status(404).send('No files found in the bucket.');
    }

    // Generate a signed URL for the file (valid for 15 minutes)
    const [signedUrl] = await latestFile.getSignedUrl({
      action: 'read',
      expires: Date.now() + 15 * 60 * 1000, // 15 minutes
    });

    // Return the signed URL
    res.json({ image_url: signedUrl });
  } catch (err) {
    console.error('Error fetching image from GCP bucket:', err);
    res.status(500).send('Internal Server Error');
  }
});

// Start the server

app.listen(port, '0.0.0.0', () => {
    console.log(`Backend server listening on http://0.0.0.0:${port}`);
  });
