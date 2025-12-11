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

export const EXAMPLE_PROMPTS: Record<string, string[]> = {
  hr_data: [
    "What is the attrition rate by department?",
    "Why do employees leave the company?",
    "What is the average monthly income by job role?",
    "Why is attrition higher in Sales department?",
    "What is the distribution of years at company for employees who left vs stayed?"
  ],
  sales_data: [
    "What is the average order value (AOV) overall, and how does it vary by acquisition channel?",
    "Why do customers return products?",
    "Which top German city recorded the highest total revenue, and what percentage of overall revenue does it represent?",
    "Why is discount affecting profit margin?",
    "How many unique customers are there, and what percentage of them made more than one purchase?"
  ]
};

export function getExamplePrompts(datasetId: string): string[] {
  return EXAMPLE_PROMPTS[datasetId] || EXAMPLE_PROMPTS.hr_data;
}