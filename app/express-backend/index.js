const express = require('express');
const cors = require('cors');
const { Storage } = require('@google-cloud/storage');

const app = express();
const port = process.env.BACKEND_PORT || 5000; // Default to port 5000 if not specified
const frontendUrl = process.env.FRONTEND_URL || 'http://localhost:80'; // Default frontend URL
const bucketName = process.env.GCP_BUCKET_NAME || 'state-sdtd-1'; // Default bucket name

// Middleware for CORS
app.use(
  cors({
    origin: frontendUrl, // Allow traffic from the frontend
  })
);

// GCP Storage Client (Path remains hardcoded as requested)
const storage = new Storage({
  keyFilename: '/tmp/key-file.json', // Hardcoded path to the GCP service account key file
});

// Route to fetch the latest image/GIF from the GCP bucket
app.get('/api/image', async (req, res) => {
  try {
    const [files] = await storage.bucket(bucketName).getFiles();

    // Sort files by creation time (newest first)
    files.sort((a, b) => new Date(b.metadata.timeCreated) - new Date(a.metadata.timeCreated));

    const latestFile = files[0];

    if (!latestFile) {
      return res.status(404).send('No files found in the bucket.');
    }

    // Generate a signed URL for the file (valid for 15 minutes)
    const [signedUrl] = await latestFile.getSignedUrl({
      action: 'read',
      expires: Date.now() + 15 * 60 * 1000, // 15 minutes
    });

    res.json({ image_url: signedUrl });
  } catch (err) {
    console.error('Error fetching image from GCP bucket:', err);
    res.status(500).send('Internal Server Error');
  }
});

// Start the backend server
app.listen(port, () => {
  console.log(`Backend is running on http://localhost:${port}`);
});