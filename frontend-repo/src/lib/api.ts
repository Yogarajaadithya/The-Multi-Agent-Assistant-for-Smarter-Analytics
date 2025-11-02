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
  "What is the attrition rate by department?",
  "Why do employees leave the company?",
  "What is the average monthly income by job role?",
  "Why is attrition higher in Sales department?",
  "What is the distribution of years at company for employees who left vs stayed?"
] as const;