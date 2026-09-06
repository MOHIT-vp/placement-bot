"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AlertTriangle, TrendingUp, BookOpen, Building2, Award, ArrowRight, ExternalLink } from "lucide-react";
import { Sidebar } from "@/components/navigation/sidebar";
import { MobileNav } from "@/components/navigation/mobile-nav";
import { ScoreGauge } from "@/components/ui/score-gauge";
import { PBBadge } from "@/components/ui/pb-badge";
import { PBButton } from "@/components/ui/pb-button";
import { Loader } from "@/components/ui/loader";
import { getDashboardByRunId } from "@/lib/api";

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

const PRIORITY_MAP: Record<string, { variant: "critical" | "high" | "medium" | "low"; label: string }> = {
  critical: { variant: "critical", label: "Critical" },
  high: { variant: "high", label: "High" },
  medium: { variant: "medium", label: "Medium" },
  low: { variant: "low", label: "Low" },
};

function BreakdownBar({ label, pts, max }: { label: string; pts: number; max: number }) {
  const pct = (pts / max) * 100;
  return (
    <div>
      <div className="flex justify-between text-xs mb-1.5">
        <span className="font-medium text-charcoal">{label}</span>
        <span className="type-data text-sm">{pts.toFixed(0)}<span className="text-bronze-dark/40">/{max}</span></span>
      </div>
      <div className="h-1.5 bg-surface-muted rounded-full overflow-hidden">
        <div
          className="h-full rounded-full bg-orange transition-all duration-700"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function DomainBar({ skill, pct }: { skill: string; pct: number }) {
  const color = pct >= 70 ? "#2D8A4E" : pct >= 40 ? "#C4820B" : "#C53030";
  return (
    <div>
      <div className="flex justify-between text-sm mb-1.5">
        <span className="font-medium text-charcoal capitalize">{skill}</span>
        <span className="text-xs font-bold" style={{ color }}>{pct}%</span>
      </div>
      <div className="h-1.5 bg-surface-muted rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

function MatchRow({ m, rank }: { m: CompanyMatch; rank: number }) {
  const color = m.match_score >= 75 ? "text-success bg-success-light" : m.match_score >= 55 ? "text-warning bg-warning-light" : "text-bronze-dark bg-surface-muted";
  return (
    <div className="flex items-center justify-between py-4 border-b border-border-subtle last:border-0 hover:bg-surface-warm/50 transition-colors px-1 -mx-1 rounded-lg">
      <div className="flex items-center gap-4 min-w-0">
        <span className="type-data text-bronze-dark/30 w-6 text-right shrink-0">{rank}</span>
        <div className="min-w-0">
          <p className="font-semibold text-charcoal text-[0.9375rem] truncate font-zodiak">{m.company}</p>
          <p className="text-xs text-bronze-dark/50">{m.role} · ₹{m.package_lpa} LPA</p>
        </div>
      </div>
      <span className={`text-xs font-bold px-2.5 py-1 rounded-full whitespace-nowrap ${color}`}>
        {m.match_score.toFixed(0)}%
      </span>
    </div>
  );
}

export default function DashboardPage() {
  const router = useRouter();

  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    // For MVP, we use localStorage to know which run is active since there is no login.
    const runId = localStorage.getItem("active_run_id");

    if (!runId) {
      // No active run at all, go to onboarding
      router.replace("/onboarding");
      return;
    }

    const fetchData = async () => {
      try {
        const dashboardData = await getDashboardByRunId(runId);
        
        if (dashboardData.status === "published" || dashboardData.has_approved_plan) {
          setData(dashboardData.data);
          setLoading(false);
        } else {
          // It's not published yet, redirect back to the tracker
          router.replace(`/assessment/${runId}`);
        }
      } catch (err) {
        console.error("Error fetching dashboard:", err);
        // If it completely fails, maybe the ID is invalid
        setLoading(false);
      }
    };

    fetchData();
  }, [router]);

  // ── Loading state ──
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-ivory">
        <div className="flex flex-col items-center gap-12 mt-10">
          <Loader />
          <p className="text-sm text-bronze-dark/50 font-medium">Loading your placement dashboard...</p>
        </div>
      </div>
    );
  }

  // ── Empty state (No data could be loaded) ──
  if (!data) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-ivory gap-6 p-8 text-center">
        <div className="w-16 h-16 rounded-[16px] bg-warning-light flex items-center justify-center">
          <AlertTriangle className="w-7 h-7 text-warning" />
        </div>
        <h1 className="type-h2 text-charcoal">Unable to load dashboard</h1>
        <p className="type-body text-bronze-dark/50 max-w-sm">
          We couldn't load your assessment data. Please start a new assessment.
        </p>
        <PBButton onClick={() => router.push("/onboarding")} size="lg">
          Start your assessment <ArrowRight className="w-4 h-4 ml-2" />
        </PBButton>
      </div>
    );
  }

  const { stats, placement_score, score_breakdown, skill_gaps, domain_coverage,
    top_companies, company_matches, roadmap, profile } = data;

  return (
    <div className="min-h-screen bg-ivory flex">
      {/* Sidebar */}
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} studentName={data.student_name} />

      {/* Main content */}
      <div className="flex-1 min-w-0">
        {/* Top bar */}
        <header className="sticky top-0 z-10 bg-ivory/90 backdrop-blur-sm border-b border-border-subtle px-6 lg:px-8 py-4 flex items-center justify-between">
          <div>
            <p className="type-body text-bronze-dark/50">
              Career readiness overview
            </p>
            <h1 className="text-lg font-semibold text-charcoal">
              {data.student_name ? `Welcome, ${data.student_name}` : "Your Dashboard"}
            </h1>
          </div>
          <div className="hidden sm:flex items-center gap-4">
            <p className="text-xs text-bronze-dark/40">AI-powered analysis · No data stored</p>
          </div>
        </header>

        <main className="px-6 lg:px-8 py-8 space-y-8 pb-24 lg:pb-8">

          {/* ── Metric Cards ── */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { label: "Placement Score", value: `${Math.round(placement_score)}/100`, sub: `Skills ${score_breakdown.skills}pts · Coding ${score_breakdown.coding.toFixed(0)}pts` },
              { label: "Skill Gaps Open", value: String(stats.gaps_open), sub: `${skill_gaps.filter(g => g.severity === "high").length} high priority` },
              { label: "Company Matches", value: String(company_matches.length), sub: `${stats.strong_matches} strong fit (≥ 70%)` },
              { label: "Problems Solved", value: String(stats.coding_solved), sub: "Self-reported" },
            ].map(card => (
              <div key={card.label} className="surface-card p-5">
                <p className="type-micro mb-2">{card.label}</p>
                <p className="text-2xl font-bold text-charcoal mb-1">{card.value}</p>
                <p className="text-xs text-bronze-dark/40">{card.sub}</p>
              </div>
            ))}
          </div>

          {/* ── Mobile Tab Selector ── */}
          <div className="flex gap-1 p-1 bg-surface-muted rounded-[12px] lg:hidden overflow-x-auto">
            {["overview", "companies", "roadmap", "skills"].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex-1 min-w-max text-sm font-semibold py-2 px-3 rounded-[10px] transition-colors capitalize whitespace-nowrap ${
                  activeTab === tab ? "bg-surface text-charcoal shadow-xs" : "text-bronze-dark/50"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* ═══════════════════════════════════════════
              OVERVIEW TAB
          ═══════════════════════════════════════════ */}
          {activeTab === "overview" && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-fade-in">

              {/* Score + breakdown */}
              <div className="lg:col-span-4 surface-card p-6 flex flex-col items-center gap-5">
                <h2 className="type-micro self-start">READINESS SCORE</h2>
                <ScoreGauge score={placement_score} />
                <div className="w-full space-y-3 mt-2">
                  <BreakdownBar label="Skill Coverage" pts={score_breakdown.skills} max={40} />
                  <BreakdownBar label="Coding Activity" pts={score_breakdown.coding} max={30} />
                  <BreakdownBar label="Projects & Experience" pts={score_breakdown.projects} max={20} />
                  <BreakdownBar label="CGPA" pts={score_breakdown.cgpa} max={10} />
                </div>
              </div>

              {/* Skill coverage */}
              <div className="lg:col-span-4 surface-card p-6">
                <h2 className="type-micro mb-5">DOMAIN COVERAGE</h2>
                <div className="space-y-4">
                  {Object.entries(domain_coverage).map(([skill, pct]) => (
                    <DomainBar key={skill} skill={skill} pct={pct} />
                  ))}
                  {Object.keys(domain_coverage).length === 0 && (
                    <p className="text-sm text-bronze-dark/40 italic">No domain coverage data — add more skills to your resume.</p>
                  )}
                </div>
              </div>

              {/* Top matches */}
              <div className="lg:col-span-4 surface-card p-6">
                <h2 className="type-micro mb-5 flex items-center gap-2">
                  <Building2 className="w-3.5 h-3.5 text-bronze" /> TOP COMPANY MATCHES
                </h2>
                <div>
                  {top_companies.map((m, i) => (
                    <MatchRow key={i} m={m} rank={i + 1} />
                  ))}
                </div>
                <button
                  onClick={() => setActiveTab("companies")}
                  className="mt-4 text-sm font-medium text-orange hover:text-orange-deep transition-colors flex items-center gap-1"
                >
                  View all matches <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* AI Summary */}
              {profile.summary && (
                <div className="lg:col-span-12 surface-warm p-6 rounded-[16px]">
                  <h2 className="type-micro mb-3 flex items-center gap-2">
                    <Award className="w-3.5 h-3.5 text-bronze" /> AI PROFILE SUMMARY
                  </h2>
                  <p className="type-body leading-relaxed">{profile.summary}</p>
                </div>
              )}
            </div>
          )}

          {/* ═══════════════════════════════════════════
              COMPANY MATCHES TAB
          ═══════════════════════════════════════════ */}
          {activeTab === "companies" && (
            <div className="animate-fade-in">
              <div className="mb-6">
                <h2 className="type-h2 mb-1">Where you fit.</h2>
                <p className="type-body text-bronze-dark/50">Companies ranked by your current profile strength.</p>
              </div>

              <div className="surface-card overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border-default bg-surface-warm">
                        {["Company", "Role", "Match", "Package", "Confidence", "Missing Skills"].map(h => (
                          <th key={h} className="text-left px-5 py-3 type-micro whitespace-nowrap">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {company_matches.map((m, i) => {
                        const matchColor = m.match_score >= 75 ? "text-success bg-success-light" : m.match_score >= 55 ? "text-warning bg-warning-light" : "text-bronze-dark bg-surface-muted";
                        return (
                          <tr key={i} className="border-b border-border-subtle hover:bg-surface-warm/50 transition-colors">
                            <td className="px-5 py-4 font-semibold text-charcoal font-zodiak">{m.company}</td>
                            <td className="px-5 py-4 text-bronze-dark/70">{m.role}</td>
                            <td className="px-5 py-4">
                              <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${matchColor}`}>
                                {m.match_score.toFixed(0)}%
                              </span>
                            </td>
                            <td className="px-5 py-4 text-charcoal">₹{m.package_lpa} LPA</td>
                            <td className="px-5 py-4">
                              <PBBadge variant={m.confidence === "High" ? "success" : m.confidence === "Moderate" ? "medium" : "low"}>
                                {m.confidence}
                              </PBBadge>
                            </td>
                            <td className="px-5 py-4 text-xs text-bronze-dark/50">
                              {m.missing_skills.length > 0 ? m.missing_skills.join(", ") : <span className="text-success font-semibold">None ✓</span>}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ═══════════════════════════════════════════
              ROADMAP TAB
          ═══════════════════════════════════════════ */}
          {activeTab === "roadmap" && (
            <div className="animate-fade-in">
              <div className="mb-6">
                <h2 className="type-h2 mb-1">Your learning roadmap.</h2>
                <p className="type-body text-bronze-dark/50">A structured plan to close your skill gaps and strengthen your placement readiness.</p>
              </div>

              {roadmap.length === 0 ? (
                <div className="surface-card p-12 text-center">
                  <div className="w-12 h-12 rounded-[14px] bg-success-light flex items-center justify-center mx-auto mb-4">
                    <TrendingUp className="w-5 h-5 text-success" />
                  </div>
                  <h3 className="font-bold text-lg text-charcoal">Excellent coverage!</h3>
                  <p className="text-sm text-bronze-dark/50 mt-1">No critical skill gaps were identified from your resume.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {roadmap.map((item, i) => {
                    const priority = PRIORITY_MAP[item.priority] || PRIORITY_MAP.low;
                    return (
                      <div key={i} className="surface-card p-5 flex items-start gap-5 hover-lift">
                        <div className="w-10 h-10 rounded-full bg-earth flex items-center justify-center text-ivory text-sm font-bold shrink-0">
                          W{item.week}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap mb-1">
                            <h3 className="font-semibold text-charcoal">{item.action}</h3>
                            <PBBadge variant={priority.variant}>{priority.label}</PBBadge>
                          </div>
                          <p className="text-sm text-bronze flex items-center gap-1.5">
                            <BookOpen className="w-3.5 h-3.5 shrink-0" />
                            {item.resource}
                          </p>
                          <p className="text-xs text-bronze-dark/40 mt-1">~{item.estimated_hours} hours estimated</p>
                        </div>
                        <div className="text-right text-xs text-bronze-dark/40 shrink-0 hidden sm:block">
                          <TrendingUp className="w-3.5 h-3.5 inline mb-0.5" /> <span className="font-semibold capitalize">{item.skill}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* ═══════════════════════════════════════════
              SKILLS TAB
          ═══════════════════════════════════════════ */}
          {activeTab === "skills" && (
            <div className="space-y-6 animate-fade-in">
              {/* Skills grid */}
              <div className="surface-card p-6">
                <h2 className="font-semibold text-charcoal mb-4">Extracted Skills ({profile.skills.length})</h2>
                <div className="flex flex-wrap gap-2">
                  {profile.skills.map((s, i) => {
                    const variant =
                      s.proficiency === "advanced" || s.proficiency === "expert" ? "success" :
                      s.proficiency === "intermediate" ? "medium" : "low";
                    return (
                      <PBBadge key={i} variant={variant}>
                        {s.name} · {s.proficiency}
                      </PBBadge>
                    );
                  })}
                </div>
              </div>

              {/* Projects */}
              {profile.projects.length > 0 && (
                <div className="surface-card p-6">
                  <h2 className="font-semibold text-charcoal mb-4">Projects ({profile.projects.length})</h2>
                  <div className="space-y-4">
                    {profile.projects.map((p, i) => (
                      <div key={i} className="p-4 surface-warm rounded-[12px]">
                        <h3 className="font-semibold text-charcoal">{p.title}</h3>
                        <p className="text-sm text-bronze-dark/60 mt-1 leading-relaxed">{p.description}</p>
                        <div className="flex flex-wrap gap-1.5 mt-3">
                          {p.technologies?.map((t, j) => (
                            <span key={j} className="text-xs bg-surface border border-border-subtle text-bronze-dark px-2 py-0.5 rounded-full">{t}</span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Experience */}
              {profile.experiences.length > 0 && (
                <div className="surface-card p-6">
                  <h2 className="font-semibold text-charcoal mb-4">Experience ({profile.experiences.length})</h2>
                  <div className="space-y-3">
                    {profile.experiences.map((e, i) => (
                      <div key={i} className="flex items-center justify-between p-4 surface-warm rounded-[12px]">
                        <div>
                          <p className="font-semibold text-charcoal">{e.role}</p>
                          <p className="text-sm text-bronze-dark/50 font-zodiak">{e.company}</p>
                        </div>
                        <span className="text-xs text-bronze-dark/40 shrink-0">{e.duration}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </main>
      </div>

      {/* Mobile nav */}
      <MobileNav activeTab={activeTab} onTabChange={setActiveTab} />
    </div>
  );
}
