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
        responseType: 'blob',
      });

      const url = URL.createObjectURL(response.data);
      setImageUrl(url);
    } catch (error) {
      console.error('Erreur lors de la récupération de l\'image:', error);
      setError('Erreur lors de la récupération de l\'image.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchImage();
    const interval = setInterval(fetchImage, 15000); // Changed to 15 seconds
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (imageUrl) {
      console.log('Image URL mise à jour:', imageUrl);
    }
  }, [imageUrl]);

  useEffect(() => {
    return () => {
      if (imageUrl) {
        URL.revokeObjectURL(imageUrl);
      }
    };
  }, [imageUrl]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-base-200 to-base-300 flex items-center justify-center p-4">
      <div className="card w-full max-w-2xl shadow-2xl bg-base-100 hover:shadow-3xl transition-shadow duration-300">
        <div className="card-body p-8">
          <h1 className="text-3xl font-bold text-center mb-6 text-primary">
            Affichage d'Image en Direct
            <span className="block mt-2 text-lg font-normal text-secondary">Mise à jour toutes les 15 secondes</span>
          </h1>

          {loading && (
            <div className="flex flex-col items-center justify-center my-8 space-y-4">
              <span className="loading loading-spinner text-primary loading-lg"></span>
              <p className="text-gray-500">Chargement de l'image...</p>
            </div>
          )}

          {error && (
            <div className="alert alert-error shadow-lg my-4">
              <div className="flex items-center space-x-2">
                <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="flex-grow text-left">{error}</span>
              </div>
            </div>
          )}

          {!loading && !error && imageUrl && (
            <div className="group relative overflow-hidden rounded-xl bg-base-200">
              <img
                src={imageUrl}
                alt="Latest from GCP Bucket"
                className="w-full h-96 object-contain transition-transform duration-500 group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            </div>
          )}

          <div className="card-actions justify-center mt-6">
            <button
              className="btn btn-primary btn-wide gap-2"
              onClick={fetchImage}
              disabled={loading}
            >
              {!loading ? (
                <>
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
                  </svg>
                  Rafraîchir
                </>
              ) : (
                'Chargement...'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;