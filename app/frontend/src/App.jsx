import React, { useEffect, useState } from 'react';
import axios from 'axios';

const App = () => {
  const [imageUrl, setImageUrl] = useState('');
  const backendUrl = process.env.REACT_APP_BACKEND_URL;

  const fetchImage = async () => {
    try {
      const response = await axios.get(`${backendUrl}/api/image`);
      setImageUrl(response.data.image_url);
    } catch (error) {
      console.error('Error fetching the image:', error);
    }
  };

  useEffect(() => {
    fetchImage();
    const interval = setInterval(fetchImage, 5000); // Récupère une image toutes les 5 secondes
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    console.log('Image URL mise à jour:', imageUrl); // Log de la mise à jour de l'état
  }, [imageUrl]);

  return (
    <div style={{ textAlign: 'center', marginTop: '50px' }}>
      <h1>Affichage d'une image toutes les 5 secondes</h1>
      {imageUrl && (
        <img
          src={`${imageUrl}?${new Date().getTime()}`} // Ajoute un timestamp pour éviter le cache
          alt="Random"
          style={{ maxWidth: '100%', height: 'auto' }}
        />
      )}
    </div>
  );
};

export default App;