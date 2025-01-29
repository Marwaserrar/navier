require('dotenv').config({ path: '/app/.env' }); // Load .env file from the mounted path
const express = require('express');
const cors = require('cors');
const { Storage } = require('@google-cloud/storage');
const path = require('path');

const app = express();
const port = 5000;

// Read the SERVER_ADDRESS from environment variables
const serverAddress = process.env.SERVER_ADDRESS || 'localhost';

// Configure CORS to allow requests from any origin
app.use(cors());

// GCP Storage Client
const storage = new Storage({
  keyFilename: '/secrets/key-file.json', // Path to the mounted service account key file
});

const bucketName = 'bucket-marwa'; // Replace with your actual GCP bucket name

/**
 * Fetch the latest image for a given pod ID from the GCP bucket.
 * @param {number} podId - The pod number (1 to 5).
 */
const getLatestPodImage = async (podId) => {
  try {
    // List all files in the bucket
    const [files] = await storage.bucket(bucketName).getFiles();

    if (!files.length) {
      throw new Error('No files found in the bucket.');
    }

    // Filter files based on the pod prefix (e.g., "pod-1_simulation_plot_")
    const podPrefix = `simulation_results/pod-${podId}_simulation_plot_`;
    const podFiles = files.filter(file => file.name.startsWith(podPrefix));

    if (!podFiles.length) {
      throw new Error(`No images found for pod-${podId}`);
    }

    // Sort by timestamp (descending) to get the latest
    podFiles.sort((a, b) => new Date(b.metadata.timeCreated) - new Date(a.metadata.timeCreated));

    return podFiles[0]; // Return the latest file
  } catch (err) {
    console.error(`Error fetching latest image for pod-${podId}:`, err.message);
    return null;
  }
};

// Define 5 endpoints to fetch the latest image for each pod
[1, 2, 3, 4, 5].forEach(podId => {
  app.get(`/api/image/${podId}`, async (req, res) => {
    const latestFile = await getLatestPodImage(podId);

    if (!latestFile) {
      return res.status(404).send(`No image found for pod-${podId}`);
    }

    // Retrieve file from GCP
    const file = storage.bucket(bucketName).file(latestFile.name);

    // Fetch file metadata
    const [metadata] = await file.getMetadata();
    const contentType = metadata.contentType || 'application/octet-stream';

    // Set headers for the response
    res.setHeader('Content-Type', contentType);
    res.setHeader('Content-Disposition', `inline; filename="${path.basename(latestFile.name)}"`);

    // Create a read stream and pipe it to the response
    const readStream = file.createReadStream();

    readStream.on('error', (err) => {
      console.error(`Error reading file from GCP for pod-${podId}:`, err);
      res.status(500).send('Internal Server Error');
    });

    readStream.pipe(res);
  });
});

app.listen(port, '0.0.0.0', () => {
  console.log(`Backend server listening on http://0.0.0.0:${port}`);
});