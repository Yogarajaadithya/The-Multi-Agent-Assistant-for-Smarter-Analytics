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
export async function sendAnalyticsQuery(question, includeVisualization = true) {
  console.log('Sending analytics query to:', `${BACKEND_BASE_URL}/analyze`);
  console.log('Query:', question);
  
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
    });
    
    console.log('Response status:', res.status);
    if (!res.ok) {
      const errorText = await res.text();
      console.error('Error response:', errorText);
      throw new Error(`Backend error: ${res.status} - ${errorText}`);
    }
    
    const data = await res.json();
    console.log('Response data:', data);
    console.log('Question type detected:', data.question_type);
    return data; // { success, question_type, sql, data, visualization, hypotheses, statistical_results }
  } catch (error) {
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
