"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, TrendingUp, AlertTriangle, CheckCircle, BookOpen, Building2, Award } from "lucide-react";

type CompanyMatch = {
  company: string;
  role: string;
  match_score: number;
  confidence: string;
  package_lpa: number;
  matched_skills: string[];
  missing_skills: string[];
};

type RoadmapItem = {
  week: number;
  skill: string;
  action: string;
  resource: string;
  estimated_hours: number;
  priority: string;
};

type DashboardData = {
  student_name: string;
  github_username?: string;
  leetcode_handle?: string;
  placement_score: number;
  score_breakdown: { skills: number; coding: number; projects: number; cgpa: number };
  skill_gaps: { skill: string; severity: string; coverage: number }[];
  domain_coverage: Record<string, number>;
  company_matches: CompanyMatch[];
  top_companies: CompanyMatch[];
  roadmap: RoadmapItem[];
  profile: {
    skills: { name: string; proficiency: string }[];
    projects: { title: string; description: string; technologies: string[] }[];
    experiences: { company: string; role: string; duration: string }[];
    education?: { degree: string; institution: string; gpa?: number };
    summary: string;
  };
  stats: {
    total_skills: number;
    total_projects: number;
    total_experiences: number;
    coding_solved: number;
    gaps_open: number;
    strong_matches: number;
  };
};

const PRIORITY_COLOR: Record<string, string> = {
  critical: "bg-red-100 text-red-700 border-red-200",
  high: "bg-amber-100 text-amber-700 border-amber-200",
  medium: "bg-blue-100 text-blue-700 border-blue-200",
  low: "bg-slate-100 text-slate-600 border-slate-200",
};

const SEVERITY_COLOR: Record<string, string> = {
  high: "bg-red-500",
  medium: "bg-amber-500",
  low: "bg-blue-400",
};

function ScoreRing({ score }: { score: number }) {
  const r = 54;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = score >= 75 ? "#22c55e" : score >= 55 ? "#f59e0b" : "#ef4444";

  return (
    <div className="relative w-40 h-40 flex items-center justify-center mx-auto">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r={r} fill="none" stroke="#e2e8f0" strokeWidth="10" />
        <circle cx="60" cy="60" r={r} fill="none" stroke={color} strokeWidth="10"
          strokeDasharray={circ} strokeDashoffset={offset}
          strokeLinecap="round" style={{ transition: "stroke-dashoffset 1s ease" }} />
      </svg>
      <div className="absolute text-center">
        <span className="text-4xl font-extrabold text-slate-800">{Math.round(score)}</span>
        <span className="block text-sm text-slate-500 font-medium">/ 100</span>
      </div>
    </div>
  );
}

function MatchBadge({ score }: { score: number }) {
  const color = score >= 75 ? "bg-emerald-600" : score >= 55 ? "bg-amber-500" : "bg-slate-500";
  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold text-white ${color}`}>
      {score.toFixed(0)}% match
    </span>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"overview" | "companies" | "roadmap" | "skills">("overview");

  useEffect(() => {
    const raw = localStorage.getItem("placement_result");
    if (raw) {
      try {
        setData(JSON.parse(raw));
      } catch {
        /* invalid data */
      }
    }
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-slate-300 border-t-blue-600 rounded-full animate-spin" />
          <p className="text-slate-500 font-medium">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 gap-6 p-8 text-center">
        <div className="w-20 h-20 rounded-full bg-amber-100 flex items-center justify-center">
          <AlertTriangle className="w-10 h-10 text-amber-600" />
        </div>
        <h1 className="text-2xl font-bold text-slate-800">No Analysis Found</h1>
        <p className="text-slate-500 max-w-sm">
          You have not yet submitted your resume for analysis. Please go through the onboarding form first.
        </p>
        <button onClick={() => router.push("/onboarding")}
          className="px-8 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-colors shadow">
          Start Evaluation
        </button>
      </div>
    );
  }

  const { stats, placement_score, score_breakdown, skill_gaps, domain_coverage,
    top_companies, company_matches, roadmap, profile } = data;

  const TABS = [
    { key: "overview", label: "Overview" },
    { key: "companies", label: `Company Matches (${company_matches.length})` },
    { key: "roadmap", label: "Learning Roadmap" },
    { key: "skills", label: `Skills (${profile.skills.length})` },
  ] as const;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 font-sans">
      {/* ── Header ── */}
      <header className="bg-white border-b border-slate-200 shadow-sm sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-8 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-slate-800 leading-tight">
              Placement Readiness & Career Intelligence Portal
            </h1>
            <p className="text-xs text-slate-500 mt-0.5">AI-powered career analysis · No data stored</p>
          </div>
          <button onClick={() => router.push("/onboarding")}
            className="flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors">
            <ArrowLeft className="w-4 h-4" /> Re-analyse
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-8 py-8 space-y-8">

        {/* ── Top stat cards ── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: "Placement Score", value: `${Math.round(placement_score)}/100`, sub: `Skills ${score_breakdown.skills}pts · Coding ${score_breakdown.coding.toFixed(0)}pts` },
            { label: "Skill Gaps Open", value: stats.gaps_open, sub: `${skill_gaps.filter(g => g.severity === "high").length} high priority` },
            { label: "Company Matches", value: company_matches.length, sub: `${stats.strong_matches} strong fit (≥ 70%)` },
            { label: "Problems Solved", value: stats.coding_solved, sub: "Self-reported" },
          ].map(card => (
            <div key={card.label} className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 flex flex-col justify-between">
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">{card.label}</h3>
              <div className="text-3xl font-extrabold text-slate-800">{card.value}</div>
              <p className="text-xs text-slate-500 mt-2">{card.sub}</p>
            </div>
          ))}
        </div>

        {/* ── Tabs ── */}
        <div className="flex gap-1 bg-white border border-slate-200 rounded-xl p-1 shadow-sm w-full overflow-x-auto">
          {TABS.map(t => (
            <button key={t.key} onClick={() => setActiveTab(t.key)}
              className={`flex-1 min-w-max text-sm font-semibold py-2 px-4 rounded-lg transition-colors whitespace-nowrap
                ${activeTab === t.key ? "bg-blue-600 text-white shadow" : "text-slate-600 hover:bg-slate-100"}`}>
              {t.label}
            </button>
          ))}
        </div>

        {/* ── Overview tab ── */}
        {activeTab === "overview" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

            {/* Score + breakdown */}
            <div className="lg:col-span-4 bg-white rounded-xl border border-slate-200 shadow-sm p-6 flex flex-col items-center gap-4">
              <h2 className="text-base font-bold text-slate-700 self-start">Readiness Score</h2>
              <ScoreRing score={placement_score} />
              <div className="w-full space-y-3 mt-2">
                {[
                  { label: "Skill Coverage", pts: score_breakdown.skills, max: 40 },
                  { label: "Coding Activity", pts: score_breakdown.coding, max: 30 },
                  { label: "Projects & Experience", pts: score_breakdown.projects, max: 20 },
                  { label: "CGPA", pts: score_breakdown.cgpa, max: 10 },
                ].map(b => (
                  <div key={b.label}>
                    <div className="flex justify-between text-xs text-slate-500 mb-1">
                      <span>{b.label}</span>
                      <span className="font-semibold">{b.pts.toFixed(0)} / {b.max}</span>
                    </div>
                    <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500 rounded-full" style={{ width: `${(b.pts / b.max) * 100}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Skill gaps */}
            <div className="lg:col-span-4 bg-white rounded-xl border border-slate-200 shadow-sm p-6">
              <h2 className="text-base font-bold text-slate-700 mb-5">Skill Gap Analysis</h2>
              <div className="space-y-4">
                {Object.entries(domain_coverage).map(([skill, pct]) => (
                  <div key={skill}>
                    <div className="flex justify-between text-sm mb-1.5">
                      <span className="font-medium capitalize">{skill}</span>
                      <span className={`text-xs font-bold ${pct >= 70 ? "text-green-600" : pct >= 40 ? "text-amber-600" : "text-red-500"}`}>
                        {pct}%
                      </span>
                    </div>
                    <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${pct >= 70 ? "bg-green-500" : pct >= 40 ? "bg-amber-500" : "bg-red-500"}`}
                        style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                ))}
                {Object.keys(domain_coverage).length === 0 && (
                  <p className="text-sm text-slate-400 italic">No domain coverage data found — add more skills to your resume.</p>
                )}
              </div>
            </div>

            {/* Top 5 matches */}
            <div className="lg:col-span-4 bg-white rounded-xl border border-slate-200 shadow-sm p-6">
              <h2 className="text-base font-bold text-slate-700 mb-5 flex items-center gap-2">
                <Building2 className="w-4 h-4 text-blue-500" /> Top Company Matches
              </h2>
              <div className="space-y-4">
                {top_companies.map((m, i) => (
                  <div key={i} className="flex items-center justify-between pb-3 border-b border-slate-100 last:border-0 last:pb-0">
                    <div>
                      <p className="text-sm font-semibold">{m.company}</p>
                      <p className="text-xs text-slate-500">{m.role} · ₹{m.package_lpa} LPA</p>
                    </div>
                    <MatchBadge score={m.match_score} />
                  </div>
                ))}
              </div>
            </div>

            {/* Summary */}
            {profile.summary && (
              <div className="lg:col-span-12 bg-blue-50 border border-blue-200 rounded-xl p-5">
                <h2 className="text-sm font-bold text-blue-800 mb-2 flex items-center gap-2">
                  <Award className="w-4 h-4" /> AI Profile Summary
                </h2>
                <p className="text-sm text-blue-900 leading-relaxed">{profile.summary}</p>
              </div>
            )}
          </div>
        )}

        {/* ── Company matches tab ── */}
        {activeTab === "companies" && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  {["Company", "Role", "Match", "Package", "Confidence", "Missing Skills"].map(h => (
                    <th key={h} className="text-left px-5 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {company_matches.map((m, i) => (
                  <tr key={i} className="hover:bg-slate-50 transition-colors">
                    <td className="px-5 py-4 font-semibold">{m.company}</td>
                    <td className="px-5 py-4 text-slate-600">{m.role}</td>
                    <td className="px-5 py-4"><MatchBadge score={m.match_score} /></td>
                    <td className="px-5 py-4 text-slate-600">₹{m.package_lpa} LPA</td>
                    <td className="px-5 py-4">
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                        m.confidence === "High" ? "bg-green-100 text-green-700"
                          : m.confidence === "Moderate" ? "bg-amber-100 text-amber-700"
                          : "bg-slate-100 text-slate-600"}`}>{m.confidence}</span>
                    </td>
                    <td className="px-5 py-4 text-slate-500 text-xs">
                      {m.missing_skills.length > 0 ? m.missing_skills.join(", ") : <span className="text-green-600 font-semibold">None ✓</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* ── Roadmap tab ── */}
        {activeTab === "roadmap" && (
          <div className="space-y-4">
            {roadmap.length === 0 && (
              <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
                <CheckCircle className="w-10 h-10 text-green-500 mx-auto mb-3" />
                <h3 className="font-bold text-lg">Excellent coverage!</h3>
                <p className="text-slate-500 text-sm mt-1">No critical skill gaps were identified from your resume.</p>
              </div>
            )}
            {roadmap.map((item, i) => (
              <div key={i} className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 flex items-start gap-5">
                <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                  W{item.week}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <h3 className="font-bold">{item.action}</h3>
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border capitalize ${PRIORITY_COLOR[item.priority] || PRIORITY_COLOR.low}`}>
                      {item.priority}
                    </span>
                  </div>
                  <p className="text-sm text-blue-700 font-medium">
                    <BookOpen className="w-3.5 h-3.5 inline mr-1.5 mb-0.5" />
                    {item.resource}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">~{item.estimated_hours} hours estimated</p>
                </div>
                <div className="text-right text-xs text-slate-400 flex-shrink-0">
                  <TrendingUp className="w-4 h-4 inline mb-0.5" /> Skill: <span className="font-semibold capitalize">{item.skill}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ── Skills tab ── */}
        {activeTab === "skills" && (
          <div className="space-y-6">
            {/* Skills grid */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
              <h2 className="font-bold text-slate-700 mb-4">Extracted Skills ({profile.skills.length})</h2>
              <div className="flex flex-wrap gap-2">
                {profile.skills.map((s, i) => (
                  <span key={i} className={`px-3 py-1.5 rounded-full text-xs font-semibold border
                    ${s.proficiency === "advanced" || s.proficiency === "expert" ? "bg-green-100 text-green-800 border-green-200"
                      : s.proficiency === "intermediate" ? "bg-blue-100 text-blue-800 border-blue-200"
                      : "bg-slate-100 text-slate-700 border-slate-200"}`}>
                    {s.name} · {s.proficiency}
                  </span>
                ))}
              </div>
            </div>

            {/* Projects */}
            {profile.projects.length > 0 && (
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
                <h2 className="font-bold text-slate-700 mb-4">Projects ({profile.projects.length})</h2>
                <div className="space-y-4">
                  {profile.projects.map((p, i) => (
                    <div key={i} className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                      <h3 className="font-semibold">{p.title}</h3>
                      <p className="text-sm text-slate-600 mt-1 leading-relaxed">{p.description}</p>
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        {p.technologies?.map((t, j) => (
                          <span key={j} className="text-xs bg-white border border-slate-200 text-slate-600 px-2 py-0.5 rounded-full">{t}</span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Experience */}
            {profile.experiences.length > 0 && (
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
                <h2 className="font-bold text-slate-700 mb-4">Experience ({profile.experiences.length})</h2>
                <div className="space-y-3">
                  {profile.experiences.map((e, i) => (
                    <div key={i} className="flex items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-100">
                      <div>
                        <p className="font-semibold">{e.role}</p>
                        <p className="text-sm text-slate-500">{e.company}</p>
                      </div>
                      <span className="text-xs text-slate-400">{e.duration}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
