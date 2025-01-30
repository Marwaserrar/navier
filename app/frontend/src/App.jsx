import React, { useEffect, useState } from "react";
import axios from "axios";

const POD_IDS = [1, 2, 3, 4, 5];

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
    const interval = setInterval(fetchImages, 15000);
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
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
      <h1 className="text-2xl font-bold text-primary mb-4">
        🎯 Pod Image Dashboard
      </h1>

      {loading && <p className="text-gray-500 mb-4">Chargement des images...</p>}

      {error && (
        <div className="bg-red-100 text-red-600 p-2 rounded-lg mb-4 w-80 text-center">
          {error}
        </div>
      )}

      <div className="flex gap-4">
        {POD_IDS.map((podId) => (
          <div key={podId} className="w-32 h-44 p-2 bg-white shadow-lg rounded-lg flex flex-col items-center">
            <div className="w-28 h-28 bg-gray-200 rounded-md flex items-center justify-center">
              {images[podId] ? (
                <img
                  src={images[podId]}
                  alt={`Pod-${podId}`}
                  className="w-full h-full object-cover rounded-md"
                />
              ) : (
                <span className="text-gray-500 text-sm">Pas d'image</span>
              )}
            </div>
            <h2 className="text-sm font-semibold mt-2 text-gray-700">Pod-{podId}</h2>
          </div>
        ))}
      </div>

      <button
        className="mt-6 bg-blue-500 text-white px-4 py-2 rounded-lg shadow-md hover:bg-blue-600 transition"
        onClick={fetchImages}
        disabled={loading}
      >
        {loading ? "Chargement..." : "Rafraîchir"}
      </button>
    </div>
  );
};

export default App;
