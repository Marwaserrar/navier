import React, { useEffect, useState } from 'react';
import axios from 'axios';

const App = () => {
  const [imageUrl, setImageUrl] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchImage = async () => {
    try {
      setLoading(true);
      setError('');

      const response = await axios.get('/api/image', {
        responseType: 'blob', // Important: Receive data as a Blob
      });

      // Create a local URL of the image blob
      const url = URL.createObjectURL(response.data);
      setImageUrl(url);

      // Revoke the object URL after image is loaded to free memory
      // Optional: You can implement cleanup if needed
    } catch (error) {
      console.error('Erreur lors de la récupération de l\'image:', error);
      setError('Erreur lors de la récupération de l\'image.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchImage();
    const interval = setInterval(fetchImage, 5000); // Récupère une image toutes les 5 secondes
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (imageUrl) {
      console.log('Image URL mise à jour:', imageUrl);
    }
  }, [imageUrl]);

  return (
    <div className="min-h-screen bg-base-200 flex items-center justify-center p-4">
      <div className="card w-full max-w-md shadow-xl bg-base-100">
        <div className="card-body">
          <h1 className="text-2xl font-bold text-center mb-4">Affichage d'une Image</h1>

          {loading && (
            <div className="flex justify-center my-4">
              <div className="radial-progress animate-spin" style={{ '--value': 70 }}>Loading...</div>
            </div>
          )}

          {error && (
            <div className="alert alert-error shadow-lg my-4">
              <div>
                <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>{error}</span>
              </div>
            </div>
          )}

          {!loading && !error && imageUrl && (
            <div className="flex justify-center">
              <img
                src={`${imageUrl}?${new Date().getTime()}`} // Ajoute un timestamp pour éviter le cache
                alt="Random"
                className="rounded-lg shadow-md max-h-96"
              />
            </div>
          )}

          <div className="card-actions justify-center mt-4">
            <button
              className="btn btn-primary"
              onClick={fetchImage}
              disabled={loading}
            >
              Rafraîchir l'Image
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;