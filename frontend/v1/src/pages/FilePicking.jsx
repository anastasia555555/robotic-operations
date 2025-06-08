import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authFetch } from '../components/AuthFetcher.jsx';
import './FilePicking.css';


export default function OpPlanning() {
  const [patients, setPatients] = useState([]);
  const [operationTypes, setOperationTypes] = useState([]);
  const [boneModels, setBoneModels] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState('');
  const [selectedOperationType, setSelectedOperationType] = useState('');
  const [selectedBoneModel, setSelectedBoneModel] = useState('');
  const [operationPlans, setOperationPlans] = useState([]);

  const navigate = useNavigate();

  useEffect(() => {
    authFetch('http://127.0.0.1:8000/patients/list_patients')
      .then((response) => response.json())
      .then((data) => setPatients(data));

    authFetch('http://127.0.0.1:8000/operation_plans/list_operation_types')
      .then((response) => response.json())
      .then((data) => setOperationTypes(data));

    authFetch('http://127.0.0.1:8000/operation_plans/list_operation_plans')
      .then((response) => response.json())
      .then((data) => setOperationPlans(data));
  }, []);

  useEffect(() => {
    if (selectedPatient) {
      authFetch(`http://127.0.0.1:8000/3d_bone_models/list_by_patient?i_patient=${selectedPatient}`)
        .then((response) => response.json())
        .then((data) => setBoneModels(data));
    }
  }, [selectedPatient]);

  const handleSubmit = () => {
    const currentDate = new Date();
    const formattedDate = currentDate.toISOString().slice(0, 19).replace('T', ' ');
    const patient = patients.find((p) => p.i_patient === parseInt(selectedPatient, 10));
    const boneModel = boneModels.find((model) => model.i_3d_bone_model === parseInt(selectedBoneModel, 10));
    const name = `${formattedDate} ${patient.first_name} ${patient.last_name} ${boneModel.file_name}`;

    authFetch('http://127.0.0.1:8000/operation_plans/add_opplan', {
      method: 'POST',
      body: JSON.stringify({
        i_operation_type: selectedOperationType,
        i_patient: selectedPatient,
        name: name,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        const i_operation_plan = parseInt(data.i_operation_plan, 10);
        const boneModelId = parseInt(selectedBoneModel, 10);

        const url = `http://127.0.0.1:8000/operation_plans/assign_bone_model?i_operation_plan=${i_operation_plan}&i_3d_bone_model=${boneModelId}`;

        authFetch(url, {
          method: 'POST',
        })
          .then((response) => response.json())
          .then((data) => {
            console.log('Bone model assigned:', data);
          })
          .catch((error) => console.error('Error assigning bone model:', error));

        navigate(`/op-planning?id=${i_operation_plan}`);
      })
      .catch((error) => console.error('Error adding operation plan:', error));
  };

  const handleOperationPlanClick = (operationPlanId) => {
    navigate(`/op-planning?id=${operationPlanId}`);
  };

  const handleDeleteOperationPlan = (operationPlanId) => {
    authFetch(`http://127.0.0.1:8000/operation_plans/delete_opplan?i_operation_plan=${operationPlanId}`, {
      method: 'DELETE',
    })
      .then((response) => response.json())
      .then(() => {
        setOperationPlans(operationPlans.filter((plan) => plan.i_operation_plan !== operationPlanId));
        console.log(`Operation Plan with ID ${operationPlanId} deleted`);
      })
      .catch((error) => console.error('Error deleting operation plan:', error));
  };

  return (
    <div className="main-content-item-files">
      <div className="operation-menu">
        <h1>Create operation plan</h1>

        <div className="field-row">
          <label>Patient:</label>
          <select
            value={selectedPatient}
            onChange={(e) => setSelectedPatient(e.target.value)}
          >
            <option value="">Select Patient</option>
            {patients.map((patient) => (
              <option key={patient.i_patient} value={patient.i_patient}>
                {patient.first_name} {patient.last_name}
              </option>
            ))}
          </select>
        </div>

        <div className="field-row">
          <label>Type:</label>
          <select
            value={selectedOperationType}
            onChange={(e) => setSelectedOperationType(e.target.value)}
          >
            <option value="">Select Operation Type</option>
            {operationTypes.map((operation) => (
              <option key={operation.i_operation_type} value={operation.i_operation_type}>
                {operation.name}
              </option>
            ))}
          </select>
        </div>

        <div className="field-row">
          <label>Bone Model:</label>
          <select
            value={selectedBoneModel}
            onChange={(e) => setSelectedBoneModel(e.target.value)}
            disabled={!selectedPatient}
          >
            <option value="">Select Bone Model</option>
            {boneModels.map((model) => (
              <option key={model.i_3d_bone_model} value={model.i_3d_bone_model}>
                {model.file_name}
              </option>
            ))}
          </select>
        </div>

        <button onClick={handleSubmit} disabled={!selectedOperationType || !selectedBoneModel || !selectedPatient}>
          Create Operation Plan
        </button>

        <h2>Existing operation plans:</h2>

        <div className="existing-operation-plans">
          <div className="operation-plans-list">
            {operationPlans.map((plan) => (
              <div key={plan.i_operation_plan} className="operation-plan-item">
                <span onClick={() => handleOperationPlanClick(plan.i_operation_plan)}>
                  {plan.name}
                </span>
                <button onClick={() => handleDeleteOperationPlan(plan.i_operation_plan)}>
                  <img src="trash_can.png" alt="Delete" width="20" height="20" />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
