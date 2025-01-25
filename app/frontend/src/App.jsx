import React, { useEffect, useState } from 'react';
import axios from 'axios';

const App = () => {
  const [imageUrl, setImageUrl] = useState('');

  const serverAddress = process.env.REACT_APP_SERVER_ADDRESS || window.env.SERVER_ADDRESS;

  const fetchImage = async () => {
    try {
      const response = await axios.get(`http://${serverAddress}:5000/api/image`);
      console.log('Image reçue:', response.data.image_url); // Log de l'URL reçue
      setImageUrl(response.data.image_url);
    } catch (error) {
      console.error('Erreur lors de la récupération de l\'image:', error);
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