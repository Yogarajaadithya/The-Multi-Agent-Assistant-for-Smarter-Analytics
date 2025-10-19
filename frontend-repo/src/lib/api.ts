export type AgentName = "planner" | "eda" | "stats" | "simulation" | "viz" | "insights";

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

export type AnalyzeResponse = {
  activity: {
    agent: AgentName;
    status: "pending" | "running" | "done";
  }[];
  eda?: {
    summary: Record<string, number | string>;
    preview: Array<Record<string, any>>;
  };
  stats?: {
    test: string;
    statistic: number;
    p_value: number;
    effect_size?: number;
    note?: string;
  };
  viz?: {
    spec?: any; // placeholder for Plotly/ECharts spec
  };
  audit?: {
    sql?: string;
    steps?: string[];
    model?: string;
  };
  insights?: {
    text: string;
    suggestions: string[];
  };
};

export const EXAMPLE_PROMPTS = [
  "What is the attrition rate by department?",
  "Why is attrition higher in Sales?",
  "What if Work-Life Balance increases by 1 for tenure < 1 year?"
] as const;

export const MOCK_ANALYZE_RESPONSE: AnalyzeResponse = {
  activity: [
    { agent: "planner", status: "done" },
    { agent: "eda", status: "done" },
    { agent: "stats", status: "done" },
    { agent: "simulation", status: "pending" },
    { agent: "viz", status: "pending" },
    { agent: "insights", status: "pending" }
  ],
  eda: {
    summary: {
      total_employees: 1470,
      departments: 3,
      avg_tenure: 7.2,
      attrition_rate: 0.16
    },
    preview: [
      { department: "Sales", employees: 450, attrition: "21%" },
      { department: "Engineering", employees: 620, attrition: "12%" },
      { department: "Support", employees: 400, attrition: "15%" }
    ]
  },
  stats: {
    test: "Chi-square test of independence",
    statistic: 15.23,
    p_value: 0.0005,
    effect_size: 0.32,
    note: "Significant association between department and attrition"
  },
  viz: {
    spec: {
      type: "bar",
      data: [
        ["Sales", 0.21],
        ["Engineering", 0.12],
        ["Support", 0.15]
      ]
    }
  },
  audit: {
    sql: `SELECT department,
       COUNT(*) as employees,
       AVG(CASE WHEN attrition = 1 THEN 1 ELSE 0 END) as attrition_rate
FROM employees
GROUP BY department
ORDER BY attrition_rate DESC`,
    steps: [
      "Load employee data",
      "Calculate department-wise metrics",
      "Apply statistical tests",
      "Generate visualizations"
    ]
  },
  insights: {
    text: "Sales department shows significantly higher attrition (21%) compared to other departments. This may be related to higher stress levels and lower work-life balance scores observed in the Sales team.",
    suggestions: [
      "How does work-life balance compare across departments?",
      "Is there a correlation between tenure and attrition in Sales?",
      "What are the key factors driving Sales attrition?"
    ]
  }
};

export async function analyze(query: string): Promise<AnalyzeResponse> {
  // Simulate API call with mock response
  await new Promise(resolve => setTimeout(resolve, 2000));
  return MOCK_ANALYZE_RESPONSE;
}