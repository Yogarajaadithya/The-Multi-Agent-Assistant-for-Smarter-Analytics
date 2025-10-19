export type Message = {
  id: string;
  role: "user" | "assistant";
  text: string;
  ts: string;
};

export type HistoryItem = {
  id: string;
  prompt: string;
  ts: string;
};

export const EXAMPLE_PROMPTS = [
  "What is the most effective machine learning model for predicting customer churn?",
  "How would you design a recommendation system for an e-commerce site?",
  "What are some best practices for data preprocessing in NLP tasks?"
] as const;