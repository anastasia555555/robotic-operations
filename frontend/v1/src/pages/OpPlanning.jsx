import './OpPlanning.css';
import PNGViewer from '../components/ModelViewer.jsx';
import React, { useEffect, useState, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { authFetch } from '../components/AuthFetcher.jsx';


export default function OpPlanning() {
  const [prosthesisModels, setProsthesisModels] = useState([]);
  const [filteredModels, setFilteredModels] = useState([]);
  const [uniqueManufacturers, setUniqueManufacturers] = useState([]);
  const [uniqueSizes, setUniqueSizes] = useState([]);
  const [uniquePolys, setUniquePolys] = useState([]);
  const [selectedManufacturer, setSelectedManufacturer] = useState('');
  const [selectedSize, setSelectedSize] = useState('');
  const [selectedPoly, setSelectedPoly] = useState('');
  const [operationType, setOperationType] = useState(null);
  const [selectedProsthesisId, setSelectedProsthesisId] = useState(null);
  const [assignedProsthesesInfo, setAssignedProsthesesInfo] = useState([]);
  const [currentView, setCurrentView] = useState("front");
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [moveDirection, setMoveDirection] = useState('up');
  const [moveValue, setMoveValue] = useState(0);

  const location = useLocation();
  const navigate = useNavigate();

  const queryParams = new URLSearchParams(location.search);
  const operationPlanId = queryParams.get('id');

  const fetchAssignedProstheses = async () => {
    if (operationPlanId) {
      try {
        const response = await authFetch(`http://127.0.0.1:8000/operation_plans/list_assigned_prosthesis_models?i_operation_plan=${operationPlanId}`);
        if (response.ok) {
          const data = await response.json();
          setAssignedProsthesesInfo(data);
        } else {
          console.error("Failed to fetch assigned prostheses:", response.statusText);
          setAssignedProsthesesInfo([]);
        }
      } catch (error) {
        console.error("Error fetching assigned prostheses:", error);
        setAssignedProsthesesInfo([]);
      }
    }
  };
  
  useEffect(() => {
    if (operationPlanId) {
      authFetch(`http://127.0.0.1:8000/operation_plans/get_opplan?i_operation_plan=${operationPlanId}`)
        .then((response) => response.json())
        .then((data) => {
          setOperationType(data.i_operation_type);
        })
        .catch((error) => console.error("Error fetching operation plan:", error));
  
      fetchAssignedProstheses();
    }
  }, [operationPlanId]);
  
  useEffect(() => {
    if (operationType) {
      authFetch(`http://127.0.0.1:8000/3d_prosthesis_models/list_by_operation_type?i_operation_type=${operationType}`)
        .then((response) => response.json())
        .then((data) => {
          setProsthesisModels(data);
  
          const uniqueManufacturers = [...new Set(data.map((model) => model.manufacturer))];
          setUniqueManufacturers(uniqueManufacturers);
        })
        .catch((error) => console.error("Error fetching prosthesis models:", error));
    }
  }, [operationType]);
  
  const handleManufacturerChange = (e) => {
    const manufacturer = e.target.value;
    setSelectedManufacturer(manufacturer);
  
    const filteredByManufacturer = prosthesisModels.filter(
      (model) => model.manufacturer.toLowerCase().trim() === manufacturer.toLowerCase().trim()
    );
    setFilteredModels(filteredByManufacturer);
  
    const uniqueSizes = [...new Set(filteredByManufacturer.map((model) => model.size))];
    setUniqueSizes(uniqueSizes);
  
    setSelectedSize('');
    setSelectedPoly('');
    setSelectedProsthesisId(null);
  };
  
  const handleSizeChange = (e) => {
    const size = e.target.value;
    setSelectedSize(size);
  
    const modelsMatchingManufacturer = prosthesisModels.filter(
      (model) => model.manufacturer.toLowerCase().trim() === selectedManufacturer.toLowerCase().trim()
    );
  
    const filteredBySize = modelsMatchingManufacturer.filter(
      (model) => String(model.size).toLowerCase().trim() === String(size).toLowerCase().trim()
    );
  
    const uniquePolys = [...new Set(filteredBySize.map((model) => model.poly).filter(poly => poly))];
    setUniquePolys(uniquePolys);
  
    setSelectedPoly('');
    setSelectedProsthesisId(null);
  };
  
  const handlePolyChange = (e) => {
    const poly = e.target.value;
    setSelectedPoly(poly);
  
    const selectedModel = prosthesisModels.find(
      (model) =>
        model.manufacturer.toLowerCase().trim() === selectedManufacturer.toLowerCase().trim() &&
        String(model.size).toLowerCase().trim() === String(selectedSize).toLowerCase().trim() &&
        String(model.poly).toLowerCase().trim() === String(poly).toLowerCase().trim()
    );
  
    if (selectedModel) {
      setSelectedProsthesisId(selectedModel.i_3d_prosthesis_model);
    } else {
      setSelectedProsthesisId(null);
    }
  };
  
  const handleChooseProsthesis = async () => {
    if (!operationPlanId || !selectedProsthesisId) {
      console.warn('Operation Plan ID or Prosthesis ID is missing.');
      return;
    }
  
    try {
      const assignedResponse = await authFetch(`http://127.0.0.1:8000/operation_plans/list_assigned_prosthesis_models?i_operation_plan=${operationPlanId}`);
      const assignedProstheses = await assignedResponse.json();
  
      for (const assigned of assignedProstheses) {
        if (assigned.i_3d_prosthesis_model) {
          await authFetch(`http://127.0.0.1:8000/operation_plans/unassign_prosthesis_model?i_operation_plan=${operationPlanId}&i_3d_prosthesis_model=${assigned.i_3d_prosthesis_model}`, {
            method: 'POST',
          });
          console.log(`Unassigned prosthesis: ${assigned.i_3d_prosthesis_model}`);
        }
      }
  
      const assignResponse = await authFetch(`http://127.0.0.1:8000/operation_plans/assign_prosthetic_model?i_operation_plan=${operationPlanId}&i_3d_prosthesis_model=${selectedProsthesisId}`, {
        method: 'POST',
      });
  
      if (assignResponse.ok) {
        console.log(`Successfully assigned prosthesis: ${selectedProsthesisId}`);
        fetchAssignedProstheses();
        alert('Prosthesis selected and assigned to list successfully!');
      } else {
        console.error('Failed to assign prosthesis:', assignResponse.statusText);
        alert('Failed to assign prosthesis.');
      }
    } catch (error) {
      console.error("Error during prosthesis assignment process:", error);
      alert('An error occurred during prosthesis assignment.');
    }
  };
  
  const handleAssignProsthesisOnly = async () => {
    if (!operationPlanId || !selectedProsthesisId) {
      console.warn('Operation Plan ID or Prosthesis ID is missing for assignment.');
      alert('Please select an operation plan and a prosthesis model.');
      return;
    }
  
    try {
      const removeResponse = await authFetch(`http://127.0.0.1:8000/operation_plan_models/remove_prosthesis?i_operation_plan=${operationPlanId}`, {
        method: 'POST',
        headers: {
          'accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });
  
      if (!removeResponse.ok) {
        let errorMessage = `Failed to remove existing prosthesis: ${removeResponse.statusText}`;
        try {
          const errorBody = await removeResponse.json();
          if (errorBody && errorBody.detail) {
            errorMessage += ` - ${errorBody.detail}`;
          }
        } catch (jsonError) {}
        throw new Error(errorMessage);
      }
      console.log(`Successfully removed existing prosthesis for operation plan: ${operationPlanId}`);
  
      const assignResponse = await authFetch('http://127.0.0.1:8000/operation_plan_models/assign_prosthesis', {
        method: 'POST',
        headers: {
          'accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          i_operation_plan: Number(operationPlanId),
          i_3d_prosthesis_model: Number(selectedProsthesisId),
        }),
      });
  
      if (!assignResponse.ok) {
        let errorMessage = `Failed to assign prosthesis: ${assignResponse.statusText}`;
        try {
          const errorBody = await assignResponse.json();
          if (errorBody && errorBody.detail) {
            errorMessage += ` - ${errorBody.detail}`;
          }
        } catch (jsonError) {}
        throw new Error(errorMessage);
      }
  
      console.log(`Successfully assigned prosthesis: ${selectedProsthesisId} to operation plan: ${operationPlanId}`);
      alert('Prosthesis assigned successfully to the model!');
    } catch (error) {
      console.error("Error during prosthesis assignment:", error);
      alert(`An error occurred during assignment: ${error.message}`);
    }
  };
  
  const handleRefreshView = useCallback(() => {
    if (!operationPlanId) {
      alert('Operation Plan ID is missing. Cannot refresh view.');
      return;
    }
    setRefreshTrigger(prev => prev + 1);
    console.log("Refresh View button clicked. Triggering PNGViewer refresh.");
  }, [operationPlanId]);
  
  const handleViewChange = useCallback((viewName) => {
    if (!operationPlanId) {
      alert('Operation Plan ID is missing. Cannot change view.');
      return;
    }
    setCurrentView(viewName);
    setRefreshTrigger(prev => prev + 1);
    console.log(`Changing view to: ${viewName}`);
  }, [operationPlanId]);
  
  const handleMoveProsthesis = async () => {
    if (!operationPlanId) {
      alert('Operation Plan ID is missing. Cannot move prosthesis.');
      return;
    }
    if (moveValue === 0) {
      alert('Please enter a non-zero value to move the prosthesis.');
      return;
    }
  
    try {
      const response = await authFetch('http://127.0.0.1:8000/operation_plan_models/slide', {
        method: 'POST',
        headers: {
          'accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          i_operation_plan: Number(operationPlanId),
          direction: moveDirection,
          value: Number(moveValue),
        }),
      });
  
      if (!response.ok) {
        let errorMessage = `Failed to move prosthesis: ${response.statusText}`;
        try {
          const errorBody = await response.json();
          if (errorBody && errorBody.detail) {
            errorMessage += ` - ${errorBody.detail}`;
          }
        } catch (jsonError) {}
        throw new Error(errorMessage);
      }
  
      console.log(`Successfully moved prosthesis ${moveDirection} by ${moveValue}`);
    } catch (error) {
      console.error("Error moving prosthesis:", error);
      alert(`An error occurred while moving prosthesis: ${error.message}`);
    }
  };
  
  const handleSavePositions = async () => {
    if (!operationPlanId) {
      alert('Operation Plan ID is missing. Cannot save positions.');
      return;
    }
    try {
      const response = await authFetch(`http://127.0.0.1:8000/operation_plan_models/save_positions?i_operation_plan=${operationPlanId}`, {
        method: 'POST',
        headers: {
          'accept': 'application/json',
        },
      });
  
      if (!response.ok) {
        let errorMessage = `Failed to save positions: ${response.statusText}`;
        try {
          const errorBody = await response.json();
          if (errorBody && errorBody.detail) {
            errorMessage += ` - ${errorBody.detail}`;
          }
        } catch (jsonError) {}
        throw new Error(errorMessage);
      }
  
      console.log(`Positions saved for operation plan: ${operationPlanId}`);
      alert('Prosthesis positions saved successfully!');
    } catch (error) {
      console.error("Error saving positions:", error);
      alert(`An error occurred while saving positions: ${error.message}`);
    }
  };
  
  const handleRestorePositions = async () => {
    if (!operationPlanId) {
      alert('Operation Plan ID is missing. Cannot restore positions.');
      return;
    }
    try {
      const response = await authFetch(`http://127.0.0.1:8000/operation_plan_models/restore_positions?i_operation_plan=${operationPlanId}`, {
        method: 'POST',
        headers: {
          'accept': 'application/json',
        },
      });
  
      if (!response.ok) {
        let errorMessage = `Failed to restore positions: ${response.statusText}`;
        try {
          const errorBody = await response.json();
          if (errorBody && errorBody.detail) {
            errorMessage += ` - ${errorBody.detail}`;
          }
        } catch (jsonError) {}
        throw new Error(errorMessage);
      }
  
      console.log(`Positions restored for operation plan: ${operationPlanId}`);
      alert('Prosthesis positions restored successfully! Remember to click "Refresh View" to see changes.');
    } catch (error) {
      console.error("Error restoring positions:", error);
      alert(`An error occurred while restoring positions: ${error.message}`);
    }
  };
  
  const handleRegisterBone = async () => {
    if (!operationPlanId) {
      alert('Operation Plan ID is missing. Cannot register bone.');
      return;
    }
  
    try {
      const removeHandlerResponse = await authFetch(`http://127.0.0.1:8000/operation_plan_models/remove_handler?i_operation_plan=${operationPlanId}`, {
        method: 'DELETE',
      });
  
      if (!removeHandlerResponse.ok) {
        let errorMessage = `Failed to remove model handler: ${removeHandlerResponse.statusText}`;
        try {
          const errorBody = await removeHandlerResponse.json();
          if (errorBody && errorBody.detail) {
            errorMessage += ` - ${errorBody.detail}`;
          }
        } catch (jsonError) {}
        throw new Error(errorMessage);
      }
      console.log(`Model handler removed for operation plan: ${operationPlanId}`);
  
      navigate(`/pre-op-positioning?id=${operationPlanId}`);
    } catch (error) {
      console.error("Error during bone registration:", error);
      alert(`An error occurred during bone registration: ${error.message}`);
    }
  };


  const renderPNGViewer = () => {
    if (!operationPlanId) {
      return <p>Operation plan not provided.</p>;
    }

    const actualViewName = currentView;

    return (
      <div className={`model-view`}>
        <div className="view-controls">
          {['front', 'back', 'left_side', 'right_side', 'top', 'bottom'].map((view) => (
            <button
              key={view}
              onClick={() => handleViewChange(view)}
              className={currentView === view ? 'active' : ''}
              disabled={!operationPlanId}
            >
              {view.charAt(0).toUpperCase() + view.slice(1).replace('_', ' ')}
            </button>
          ))}
        </div>

        <PNGViewer
          i_operation_plan={operationPlanId}
          view_name={actualViewName}
          refreshTrigger={refreshTrigger}
        />
      </div>
    );
  };

  return (
    <div className="main-content-item-planing">
      <div className="model-view">
        {renderPNGViewer()}
      </div>
      <div className="implant-menu">
        <div className="full-width">
          <select
            value={selectedManufacturer}
            onChange={handleManufacturerChange}
          >
            <option value="">Select Manufacturer</option>
            {uniqueManufacturers.map((manufacturer) => (
              <option key={manufacturer} value={manufacturer}>
                {manufacturer}
              </option>
            ))}
          </select>
        </div>
        <div className="field-row">
          <label>Size</label>
          <select
            value={selectedSize}
            onChange={handleSizeChange}
            disabled={!selectedManufacturer}
          >
            <option value="">Select Size</option>
            {uniqueSizes.map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        </div>
        <div className="field-row">
          <label>Poly</label>
          <select
            value={selectedPoly}
            onChange={handlePolyChange}
            disabled={!selectedSize}
          >
            <option value="">Select Poly</option>
            {uniquePolys.map((poly) => (
              <option key={poly} value={poly}>
                {poly}
              </option>
            ))}
          </select>
        </div>
        <div className="full-width">
          <button
            onClick={handleChooseProsthesis}
            disabled={!selectedPoly || !selectedProsthesisId || !operationPlanId}
          >
            Select prosthesis
          </button>
          <button
            onClick={handleAssignProsthesisOnly}
            disabled={!selectedPoly || !selectedProsthesisId || !operationPlanId}
            style={{ marginTop: '10px' }}
          >
            Assign to scene
          </button>
          <button
            onClick={handleRefreshView}
            disabled={!operationPlanId}
            style={{ marginTop: '10px' }}
          >
            Refresh view
          </button>
        </div>

        <div className="field-row move-controls">
          <label>Move</label>
          <select
            value={moveDirection}
            onChange={(e) => setMoveDirection(e.target.value)}
          >
            <option value="up">Up</option>
            <option value="down">Down</option>
            <option value="left">Left</option>
            <option value="right">Right</option>
            <option value="forward">Forward</option>
            <option value="backward">Backward</option>
          </select>
          <input
            type="number"
            value={moveValue}
            onChange={(e) => setMoveValue(Number(e.target.value))}
            placeholder="Value"
            min="0"
          />
          <button
            onClick={handleMoveProsthesis}
            disabled={!operationPlanId || moveValue === 0}
          >
            Apply Move
          </button>
        </div>

        <div className="assigned-prostheses-display">
          <h3>Selected Prosthesis:</h3>
          {assignedProsthesesInfo.length > 0 ? (
            assignedProsthesesInfo.map((prosthesis) => (
              <div key={prosthesis.i_3d_prosthesis_model} className="assigned-prosthesis-item">
                <p>
                  <strong>Manufacturer:</strong> {prosthesis.manufacturer}
                </p>
                <p>
                  <strong>Size:</strong> {prosthesis.size}
                </p>
                <p>
                  <strong>Poly:</strong> {prosthesis.poly}
                </p>
                <p>
                  <strong>File name:</strong> {prosthesis.file_name}
                </p>
              </div>
            ))
          ) : (
            <p>No prosthesis assigned.</p>
          )}
        </div>

        <div className="save-restore-buttons">
          <button
            onClick={handleSavePositions}
            disabled={!operationPlanId}
          >
            Save
          </button>
          <button
            onClick={handleRestorePositions}
            disabled={!operationPlanId}
          >
            Restore
          </button>
        </div>

        <div className="full-width" style={{ marginTop: '20px' }}>
          <button
            onClick={handleRegisterBone}
            disabled={!operationPlanId}
            className="register-bone-button"
          >
            Register bone
          </button>
        </div>
      </div>
    </div>
  );
}