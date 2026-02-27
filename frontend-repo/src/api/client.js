const BACKEND_BASE_URL = import.meta?.env?.VITE_BACKEND_URL || "http://127.0.0.1:8000/api";

export async function sendChat(messages) {
  console.log('Sending request to:', `${BACKEND_BASE_URL}/chat`);
  console.log('Request payload:', { messages });
  
  try {
    const res = await fetch(`${BACKEND_BASE_URL}/chat`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Accept": "application/json"
      },
      body: JSON.stringify({ messages }),
    });
    
    console.log('Response status:', res.status);
    if (!res.ok) {
      const errorText = await res.text();
      console.error('Error response:', errorText);
      throw new Error(`Backend error: ${res.status} - ${errorText}`);
    }
    
    const data = await res.json();
    console.log('Response data:', data);
    return data; // { content }
  } catch (error) {
    console.error('Request failed:', error);
    throw error;
  }
}

// New function for analytics queries using the Multi-Agent System (Planner Agent)
// This routes through the Planner Agent which intelligently determines whether to use:
// - Text-to-SQL + Visualization (for WHAT questions)
// - Hypothesis + Statistical Testing (for WHY questions)
export async function sendAnalyticsQuery(question, includeVisualization = true, timeoutMs = 180000) {
  console.log('Sending analytics query to:', `${BACKEND_BASE_URL}/analyze`);
  console.log('Query:', question);

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(`${BACKEND_BASE_URL}/analyze`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Accept": "application/json"
      },
      body: JSON.stringify({ 
        question,
        include_visualization: includeVisualization 
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    console.log('Response status:', res.status);
    if (!res.ok) {
      const errorText = await res.text();
      console.error('Error response:', errorText);
      throw new Error(`Backend error: ${res.status} - ${errorText}`);
    }
    
    const data = await res.json();
    console.log('Response data:', data);
    console.log('Question type detected:', data.question_type);
    return data;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error('Request timed out after 3 minutes. The simulation is taking longer than expected — please try again.');
    }
    if (error.message === 'Failed to fetch') {
      throw new Error('Cannot reach the backend. The server may be restarting — please wait a few seconds and try again.');
    }
    console.error('Request failed:', error);
    throw error;
  }
}

// Legacy function for direct SQL queries (bypasses Planner Agent)
export async function sendDirectSQLQuery(question) {
  console.log('Sending direct SQL query to:', `${BACKEND_BASE_URL}/query`);
  console.log('Query:', question);
  
  try {
    const res = await fetch(`${BACKEND_BASE_URL}/query`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Accept": "application/json"
      },
      body: JSON.stringify({ question }),
    });
    
    console.log('Response status:', res.status);
    if (!res.ok) {
      const errorText = await res.text();
      console.error('Error response:', errorText);
      throw new Error(`Backend error: ${res.status} - ${errorText}`);
    }
    
    const data = await res.json();
    console.log('Response data:', data);
    return data; // { sql, data, visualization, message }
  } catch (error) {
    console.error('Request failed:', error);
    throw error;
  }
}

// Get all available datasets
export async function getDatasets() {
  console.log('Fetching datasets from:', `${BACKEND_BASE_URL}/datasets`);
  
  try {
    const res = await fetch(`${BACKEND_BASE_URL}/datasets`, {
      method: "GET",
      headers: { 
        "Accept": "application/json"
      },
    });
    
    console.log('Response status:', res.status);
    if (!res.ok) {
      const errorText = await res.text();
      console.error('Error response:', errorText);
      throw new Error(`Backend error: ${res.status} - ${errorText}`);
    }
    
    const data = await res.json();
    console.log('Datasets:', data);
    return data; // { success, datasets, current_dataset_id }
  } catch (error) {
    console.error('Request failed:', error);
    throw error;
  }
}

// Switch to a different dataset
export async function switchDataset(datasetId) {
  console.log('Switching dataset to:', datasetId);
  
  try {
    const res = await fetch(`${BACKEND_BASE_URL}/datasets/switch?dataset_id=${datasetId}`, {
      method: "POST",
      headers: { 
        "Accept": "application/json"
      },
    });
    
    console.log('Response status:', res.status);
    if (!res.ok) {
      const errorText = await res.text();
      console.error('Error response:', errorText);
      throw new Error(`Backend error: ${res.status} - ${errorText}`);
    }
    
    const data = await res.json();
    console.log('Dataset switched:', data);
    return data; // { success, message, dataset }
  } catch (error) {
    console.error('Request failed:', error);
    throw error;
  }
}

// Get current active dataset
export async function getCurrentDataset() {
  console.log('Fetching current dataset from:', `${BACKEND_BASE_URL}/datasets/current`);
  
  try {
    const res = await fetch(`${BACKEND_BASE_URL}/datasets/current`, {
      method: "GET",
      headers: { 
        "Accept": "application/json"
      },
    });
    
    console.log('Response status:', res.status);
    if (!res.ok) {
      const errorText = await res.text();
      console.error('Error response:', errorText);
      throw new Error(`Backend error: ${res.status} - ${errorText}`);
    }
    
    const data = await res.json();
    console.log('Current dataset:', data);
    return data; // { success, dataset }
  } catch (error) {
    console.error('Request failed:', error);
    throw error;
  }
}
