import './PreOpPositioning.css';
import React, { useEffect, useState, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { authFetch } from '../components/AuthFetcher.jsx';
import PositioningViewer from '../components/PositioningViewer.jsx';

export default function PreOpPositioning() {
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const operationPlanId = queryParams.get('id');

  const [currentView, setCurrentView] = useState("front");
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [pointStatus, setPointStatus] = useState([]);
  const [predictionErrorData, setPredictionErrorData] = useState(null);

  const fetchStatus = useCallback(async () => {
    if (!operationPlanId) return;
    try {
      const res = await authFetch(`http://127.0.0.1:8000/preop_bone_positioning/get_points_status?i_operation_plan=${operationPlanId}`);
      if (res.ok) {
        const data = await res.json();
        setPointStatus(data);
      } else {
        console.error("Failed to fetch point status:", res.statusText);
      }
    } catch (e) {
      console.error("Error fetching point status:", e);
    }
  }, [operationPlanId]);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 15000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const handleRefreshView = useCallback(() => {
    if (!operationPlanId) {
      alert("Missing operation plan ID.");
      return;
    }
    setRefreshTrigger((prev) => prev + 1);
    fetchStatus();
    console.log("Bone view and point status refresh triggered.");
  }, [operationPlanId, fetchStatus]);
  

  const handleViewChange = useCallback((view) => {
    if (!operationPlanId) {
      alert("Missing operation plan ID.");
      return;
    }
    setCurrentView(view);
    setRefreshTrigger((prev) => prev + 1);
    console.log(`Changing bone view to: ${view}`);
  }, [operationPlanId]);

  const handleTestPositioningError = async () => {
    if (!operationPlanId) {
      alert("Missing operation plan ID.");
      return;
    }
  
    try {
      const errorResponse = await authFetch(`http://127.0.0.1:8000/preop_bone_positioning/get_mean_error?i_operation_plan=${operationPlanId}`);
      if (!errorResponse.ok) {
        const errorBody = await errorResponse.json();
        throw new Error(errorBody.detail || "Failed to calculate prediction error.");
      }
      const errorData = await errorResponse.json();
      console.log("Prediction error:", errorData);
  
      const removeResponse = await authFetch(`http://127.0.0.1:8000/preop_bone_positioning/remove_registered_points?i_operation_plan=${operationPlanId}`, {
        method: 'DELETE'
      });
      if (!removeResponse.ok) {
        const errorBody = await removeResponse.json();
        throw new Error(errorBody.detail || "Failed to remove previous registered points.");
      }
      console.log("Previous registered points removed.");
  
      const saveResponse = await authFetch(`http://127.0.0.1:8000/preop_bone_positioning/save_registered_points?i_operation_plan=${operationPlanId}`, {
        method: 'POST'
      });
      if (!saveResponse.ok) {
        const errorBody = await saveResponse.json();
        throw new Error(errorBody.detail || "Failed to save new registered points.");
      }
      const saveResult = await saveResponse.json();
      console.log("New registered points saved:", saveResult);
    
      setPredictionErrorData(errorData);

      setRefreshTrigger(prev => prev + 1);
      fetchStatus();
  
    } catch (error) {
      console.error("Error in positioning test:", error);
      alert(`Error: ${error.message}`);
    }
  };
  
  
  return (
    <div className="main-content-item-positioning">
      <div className="bone-view">
        <div className="view-controls">
          {['front', 'back', 'side', 'other side', 'top', 'bottom'].map((view) => (
            <button
              key={view}
              onClick={() => handleViewChange(view)}
              className={currentView === view ? 'active' : ''}
              disabled={!operationPlanId}
            >
              {view.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </button>
          ))}
        </div>

        <PositioningViewer
          i_operation_plan={operationPlanId}
          view_name={currentView}
          refreshTrigger={refreshTrigger}
        />
      </div>

      <div className="positioning-menu">
        <div className="full-width">
        <button
          onClick={handleRefreshView}
          disabled={!operationPlanId}
        >
          Refresh view
        </button>
      </div>

      <div className="registered-points-display">
      <h3>Point Registration Status:</h3>
      {pointStatus.length > 0 ? (
        <div className="registered-points-grid">
          {pointStatus.map((point) => (
            <div key={point.index} className="registered-point-item">
              <p><strong>Index:</strong> {point.index} ({point.type})</p>
              <p><strong>Model:</strong> {point.model_coords.map(c => c.toFixed(2)).join(', ')}</p>
              <p>
                <strong>World:</strong>{" "}
                {point.world_coords ? point.world_coords.map(c => c.toFixed(2)).join(', ') : "Not registered"}
              </p>
            </div>
          ))}
        </div>
      ) : (
        <p>No data available.</p>
      )}
    </div>

    <div className="full-width" style={{ marginTop: '20px' }}>
        <button
          onClick={handleTestPositioningError}
          disabled={!operationPlanId}
        >
          Calculate positioning error
        </button>
      </div>

      <h3>Mean Absolute Error (MAE):</h3>
      <div className="registered-points-grid">
        <div className="registered-point-item">
          {predictionErrorData ? (
            <>
              {predictionErrorData.prediction_indices.map((index, i) => (
                <p key={index}>
                  <strong>Index {index}:</strong> {predictionErrorData.prediction_errors[i].toFixed(5)}
                </p>
              ))}
              <p><strong>Mean Error:</strong> {predictionErrorData.mean_error.toFixed(5)}</p>
            </>
          ) : (
            <p>Not calculated</p>
          )}
        </div>
      </div>

      </div>
    </div>
  );
}
