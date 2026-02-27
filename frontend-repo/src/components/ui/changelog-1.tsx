import { ArrowUpRight } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export type ChangelogEntry = {
  version: string;
  date: string;
  title: string;
  description: string;
  items?: string[];
  image?: string;
  button?: {
    url: string;
    text: string;
  };
};

export interface Changelog1Props {
  title?: string;
  description?: string;
  entries?: ChangelogEntry[];
  className?: string;
}

export const projectEntries: ChangelogEntry[] = [
  {
    version: "v3.0 - February 2026",
    date: "Current Release",
    title: "Multi-Agent Orchestration System",
    description:
      "Complete implementation of a production-ready multi-agent AI analytics assistant that transforms natural language questions into validated statistical insights.",
    items: [
      "🧭 Planner Agent with intelligent question routing (WHAT vs WHY classification)",
      "💾 Text-to-SQL Agent with PostgreSQL integration and injection prevention",
      "📊 Visualization Agent with LLM-powered chart type selection",
      "🔬 Hypothesis Agent generating testable hypotheses for causal questions",
      "📈 Statistical Agent performing Chi-Square, t-tests, ANOVA, and correlation analysis",
    ],
    image: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&auto=format&fit=crop",
    button: {
      url: "https://github.com",
      text: "View Architecture",
    },
  },
  {
    version: "v2.5 - January 2026",
    date: "15 January 2026",
    title: "Enhanced Agent Monitoring & Multi-Dataset Support",
    description:
      "Added real-time agent activity tracking and support for multiple datasets with dynamic schema loading.",
    items: [
      "Real-time agent activity monitoring with color-coded logs",
      "Multi-dataset support (HR and Sales domains)",
      "Dynamic schema loading and context adaptation",
      "Performance metrics and timing data",
      "Expandable error details with stack traces",
      "Dataset-specific example prompts and KPI documentation",
    ],
    image: "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&auto=format&fit=crop",
  },
  {
    version: "v2.0 - December 2025",
    date: "20 December 2025",
    title: "Statistical Validation & AI-Powered Insights",
    description:
      "Integrated comprehensive statistical testing pipeline with automated test selection and AI-generated business interpretations.",
    items: [
      "Chi-Square Test for categorical associations",
      "Independent t-Test for two-group comparisons",
      "One-Way ANOVA for multi-group analysis",
      "Pearson/Spearman correlation for numerical relationships",
      "Effect size calculations and confidence intervals",
      "LLM-generated plain-English explanations of results",
    ],
    image: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&auto=format&fit=crop",
  },
  {
    version: "v1.5 - November 2025",
    date: "28 November 2025",
    title: "Smart Visualizations & Interactive Charts",
    description:
      "Implemented intelligent visualization system with automatic chart type selection based on data characteristics.",
    items: [
      "Automatic chart type selection (bar, line, scatter, box plots)",
      "Intelligent number formatting (currency, percentages, counts)",
      "Ordinal scale detection for rating variables",
      "Interactive Plotly charts with zoom, pan, and export",
      "Responsive design for mobile and desktop",
    ],
    image: "https://images.unsplash.com/photo-1543286386-713bdd548da4?w=800&auto=format&fit=crop",
  },
  {
    version: "v1.0 - November 2025",
    date: "19 November 2025",
    title: "Foundation: Multi-Agent Architecture",
    description:
      "Initial release establishing the core multi-agent framework with Planner, Text-to-SQL, and basic visualization capabilities.",
    items: [
      "FastAPI backend with Azure OpenAI integration",
      "React + TypeScript frontend with Vite",
      "PostgreSQL database with HR dataset support",
      "Natural language to SQL query generation",
      "Basic agent orchestration and routing",
      "Error handling and input validation",
    ],
    image: "https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=800&auto=format&fit=crop",
    button: {
      url: "https://github.com",
      text: "Initial Commit",
    },
  },
];

export const Changelog1 = ({
  title = "Project Evolution",
  description = "Tracking the development journey of the Multi-Agent AI Analytics Assistant",
  entries = projectEntries,
}: Changelog1Props) => {
  return (
    <section className="py-32">
      <div className="container">
        <div className="mx-auto max-w-3xl">
          <h1 className="mb-4 text-3xl font-bold tracking-tight md:text-5xl">
            {title}
          </h1>
          <p className="mb-6 text-base text-muted-foreground md:text-lg">
            {description}
          </p>
        </div>
        <div className="mx-auto mt-16 max-w-3xl space-y-16 md:mt-24 md:space-y-24">
          {entries.map((entry, index) => (
            <div
              key={index}
              className="relative flex flex-col gap-4 md:flex-row md:gap-16"
            >
              <div className="top-8 flex h-min w-64 shrink-0 items-center gap-4 md:sticky">
                <Badge variant="secondary" className="text-xs">
                  {entry.version}
                </Badge>
                <span className="text-xs font-medium text-muted-foreground">
                  {entry.date}
                </span>
              </div>
              <div className="flex flex-col">
                <h2 className="mb-3 text-lg leading-tight font-bold text-foreground/90 md:text-2xl">
                  {entry.title}
                </h2>
                <p className="text-sm text-muted-foreground md:text-base">
                  {entry.description}
                </p>
                {entry.items && entry.items.length > 0 && (
                  <ul className="mt-4 ml-4 space-y-1.5 text-sm text-muted-foreground md:text-base">
                    {entry.items.map((item, itemIndex) => (
                      <li key={itemIndex} className="list-disc">
                        {item}
                      </li>
                    ))}
                  </ul>
                )}
                {entry.image && (
                  <img
                    src={entry.image}
                    alt={`${entry.version} visual`}
                    className="mt-8 w-full rounded-lg object-cover"
                  />
                )}
                {entry.button && (
                  <Button variant="link" className="mt-4 self-end" asChild>
                    <a href={entry.button.url} target="_blank" rel="noopener noreferrer">
                      {entry.button.text} <ArrowUpRight className="h-4 w-4" />
                    </a>
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
