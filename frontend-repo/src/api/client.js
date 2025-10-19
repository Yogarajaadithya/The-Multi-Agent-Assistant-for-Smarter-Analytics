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
