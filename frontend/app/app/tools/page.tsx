import { Calculator, Cloud, Globe, Clock, Brain, CheckSquare, FileText } from "lucide-react";

const tools = [
  { name: "web_search", desc: "Search the web for current information", icon: Globe, needs: "WEB_SEARCH_API_KEY on server" },
  { name: "calculator", desc: "Safe math evaluation", icon: Calculator, needs: "Always available" },
  { name: "weather", desc: "Current weather by location", icon: Cloud, needs: "Always available" },
  { name: "date_time", desc: "Current date and time", icon: Clock, needs: "Always available" },
  { name: "memory", desc: "Search or save long-term memories", icon: Brain, needs: "Always available" },
  { name: "tasks", desc: "List, create, complete tasks", icon: CheckSquare, needs: "Always available" },
  { name: "files", desc: "List uploaded files", icon: FileText, needs: "Always available" },
];

export default function ToolsPage() {
  return (
    <div className="mx-auto max-w-lg px-4 pt-8 pb-12">
      <h1 className="text-xl font-semibold mb-2">Tools</h1>
      <p className="text-sm text-slate-muted mb-6">
        Royce can call these tools during chat when needed. No arbitrary code execution.
      </p>
      <ul className="space-y-2">
        {tools.map((t) => (
          <li key={t.name} className="royce-card px-4 py-3 flex gap-3 items-start">
            <span className="h-9 w-9 rounded-xl bg-gold-50 text-gold-500 flex items-center justify-center shrink-0">
              <t.icon size={18} />
            </span>
            <div>
              <p className="text-sm font-medium font-mono">{t.name}</p>
              <p className="text-xs text-slate-soft mt-0.5">{t.desc}</p>
              <p className="text-[11px] text-slate-muted mt-1">{t.needs}</p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
