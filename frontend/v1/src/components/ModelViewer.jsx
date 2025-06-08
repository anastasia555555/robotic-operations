import React, { useEffect, useState } from 'react';
import { authFetch } from './AuthFetcher.jsx';

export default function PNGViewer({ i_operation_plan, view_name, refreshTrigger }) {
  const [imageUrl, setImageUrl] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchImage = async () => {
      if (!i_operation_plan || isNaN(Number(i_operation_plan))) {
        const err = "Invalid Operation Plan ID provided.";
        setError(err);
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError(null);
      setImageUrl(null);

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000); // Timeout after 30 seconds

      try {
        const url = `http://127.0.0.1:8000/operation_plan_models/get_view?i_operation_plan=${i_operation_plan}&view_name=${view_name}`;
        
        const response = await authFetch(url, { signal: controller.signal });

        if (!response.ok) {
          let errorMessage = `Failed to fetch image: ${response.statusText}`;
          try {
              const errorBody = await response.json();
              if (errorBody && errorBody.detail) {
                  errorMessage += ` - ${errorBody.detail}`;
              }
          } catch (jsonError) {
              console.warn("Server response was not JSON on error:", jsonError);
          }
          throw new Error(errorMessage);
        }

        const imageBlob = await response.blob();
        const imageObjectUrl = URL.createObjectURL(imageBlob);

        setImageUrl(imageObjectUrl);
      } catch (error) {
        let displayError;
        if (error.name === "AbortError") {
          displayError = "Request timed out. Server is taking too long to respond.";
        } else {
          displayError = `Error fetching image: ${error.message}`;
        }
        setError(displayError);
      } finally {
        clearTimeout(timeoutId);
        setIsLoading(false);
      }
    };

    fetchImage();

    return () => {
      if (imageUrl) {
        URL.revokeObjectURL(imageUrl);
      }
    };
  }, [i_operation_plan, view_name, refreshTrigger]);

  return (
    <div style={{ height: '100%', width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
      {error ? (
        <p style={{ color: 'red' }}>{error}</p>
      ) : isLoading ? (
        <p>Loading {view_name} view...</p>
      ) : imageUrl ? (
        <img src={imageUrl} alt={`Operation Plan View: ${view_name}`} style={{ maxWidth: '100%', maxHeight: '100%' }} />
      ) : (
        <p>No image to display for {view_name} view.</p>
      )}
    </div>
  );
}