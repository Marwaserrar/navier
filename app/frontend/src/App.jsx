import React, { useEffect, useState } from "react";
import axios from "axios";

const POD_IDS = [1, 2, 3, 4];

const App = () => {
  const [images, setImages] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchImages = async () => {
    setLoading(true);
    setError("");
    try {
      const imageRequests = POD_IDS.map(async (podId) => {
        try {
          const response = await axios.get(`/api/image/${podId}`, {
            responseType: "blob",
          });
          const url = URL.createObjectURL(response.data);
          return { podId, url };
        } catch (error) {
          console.error(`Erreur de récupération pour pod-${podId}:`, error);
          return { podId, url: null };
        }
      });
      const results = await Promise.all(imageRequests);
      setImages(results.reduce((acc, { podId, url }) => ({ ...acc, [podId]: url }), {}));
    } catch (err) {
      console.error("Erreur lors de la récupération des images:", err);
      setError("Impossible de récupérer les images.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchImages();
    const interval = setInterval(fetchImages, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    return () => {
      Object.values(images).forEach((url) => {
        if (url) URL.revokeObjectURL(url);
      });
    };
  }, [images]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex flex-col items-center justify-center p-6 relative">
      

      {loading && <p className="text-gray-500 mb-4"></p>}
      {error && <div className="bg-red-100 text-red-600 p-2 rounded-lg mb-4 w-80 text-center">{error}</div>}

      
      <div className="absolute w-1/2 h-1/2 flex items-center justify-center p-10"> 
        {POD_IDS.map((podId, index) => {
          const positions = [
            "top-0 left-0 transform -translate-x-1/2 -translate-y-1/2",  // Haut gauche (pod 1)
            "top-0 right-0 transform translate-x-1/2 -translate-y-1/2", // Haut droit (pod 2)
            "bottom-0 left-0 transform -translate-x-1/2 translate-y-1/2", // Bas gauche (pod 3)
            "bottom-0 right-0 transform translate-x-1/2 translate-y-1/2", // Bas droit (pod 4)
             // "top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2", // Centre (pod 5)
          ];

          return (
            <div
              key={podId}
              className={`absolute ${positions[index]} w-[550px] h-[250px] bg-white shadow-lg rounded-lg flex items-center justify-center border-4 border-gray-200 hover:border-blue-500 transition-all duration-300`}
            >
              {images[podId] ? (
                <img src={images[podId]} alt={`Pod-${podId}`} className="w-full h-full object-cover rounded-lg" />
              ) : (
                <span className="text-gray-500 text-sm">N/A</span>
              )}
            </div>
          );
        })}
      </div>

      {/* <button
        className="mt-8 bg-gradient-to-r from-blue-500 to-purple-500 text-white px-6 py-3 rounded-lg shadow-md hover:from-blue-600 hover:to-purple-600 transition-all duration-300"
        onClick={fetchImages}
        disabled={loading}
      >
        {loading ? "Chargement..." : "Rafraîchir"}
      </button> */}
    </div>
  );
};

export default App;
