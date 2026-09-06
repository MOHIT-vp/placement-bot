"use client";

import { useEffect, useState } from "react";
import { getApprovalQueue, submitDecision } from "@/lib/api";
import { Users, CheckCircle, XCircle, Clock, BarChart3, ArrowLeft, FileSearch, Loader2 } from "lucide-react";
import Link from "next/link";
import { PBBadge } from "@/components/ui/pb-badge";
import { PBButton } from "@/components/ui/pb-button";
import { Loader } from "@/components/ui/loader";

export default function OfficerDashboardPage() {
  const [queueData, setQueueData] = useState<any>(null);
  const [statsData, setStatsData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const queue = await getApprovalQueue();
      setQueueData(queue);
      setStatsData(queue.stats);
      setLoading(false);
    } catch (err) {
      console.error("Failed to load officer queue:", err);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleDecide = async (runId: string, decision: "approved" | "rejected") => {
    setActionLoading(runId);
    try {
      await submitDecision(runId, decision);
      await loadData();
    } catch (err) {
      console.error("Decision failed:", err);
      alert("Failed to submit decision. Check console.");
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-ivory">
        <div className="flex flex-col items-center gap-12 mt-10">
          <Loader />
          <p className="text-sm text-bronze-dark/50 font-medium">Loading officer console...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-ivory">
      {/* Header */}
      <header className="border-b border-border-subtle bg-surface/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 py-5 flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Link href="/" className="flex items-center gap-2">
                <span className="text-2xl font-semibold text-charcoal font-stardom">NEXUS</span>
              </Link>
              <span className="text-bronze-dark/30 mx-1">·</span>
              <PBBadge variant="medium">Officer Console</PBBadge>
            </div>
            <h1 className="type-h2">Placement Intelligence</h1>
            <p className="type-body text-bronze-dark/50 mt-1">
              Review and publish student readiness evaluations.
            </p>
          </div>
          <Link href="/" className="text-sm font-medium text-bronze-dark/60 hover:text-charcoal transition-colors flex items-center gap-1.5">
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Portal
          </Link>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 lg:px-8 py-8 space-y-8 animate-fade-in">

        {/* ── KPI Cards ── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="surface-card p-5">
            <div className="flex items-center gap-2 mb-2">
              <BarChart3 className="w-4 h-4 text-bronze-dark/40" />
              <span className="type-micro">Total Evaluations</span>
            </div>
            <span className="text-3xl font-bold text-charcoal">{statsData.total_runs}</span>
          </div>
          <div className="surface-card p-5 border-t-2 border-t-warning/40">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="w-4 h-4 text-warning" />
              <span className="type-micro">Pending Review</span>
            </div>
            <span className="text-3xl font-bold text-warning">{statsData.pending_reviews}</span>
          </div>
          <div className="surface-card p-5 border-t-2 border-t-success/40">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="w-4 h-4 text-success" />
              <span className="type-micro">Approval Rate</span>
            </div>
            <span className="text-3xl font-bold text-success">{statsData.approval_rate_percent}%</span>
          </div>
          <div className="surface-card p-5">
            <div className="flex items-center gap-2 mb-2">
              <Users className="w-4 h-4 text-bronze-dark/40" />
              <span className="type-micro">Published</span>
            </div>
            <span className="text-3xl font-bold text-charcoal">{statsData.published_versions}</span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* ── Pending Queue ── */}
          <div className="lg:col-span-2 space-y-4">
            <h2 className="type-h3">Pending Evaluations</h2>

            {queueData.pending_runs.length === 0 ? (
              <div className="surface-card p-12 text-center">
                <div className="w-14 h-14 rounded-[14px] bg-surface-muted flex items-center justify-center mx-auto mb-4">
                  <FileSearch className="w-6 h-6 text-bronze-dark/30" />
                </div>
                <p className="font-semibold text-charcoal mb-1">No evaluations waiting for review.</p>
                <p className="text-sm text-bronze-dark/40">New submissions will appear here automatically.</p>
              </div>
            ) : (
              <div className="surface-card divide-y divide-border-subtle">
                {queueData.pending_runs.map((run: any) => (
                  <div key={run.run_id} className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-surface-warm/50 transition-colors">
                    <div>
                      <div className="flex items-center gap-3 mb-1">
                        <span className="font-semibold text-charcoal">{run.student_id}</span>
                        <PBBadge variant="high">
                          <Clock className="w-3 h-3 mr-1" />
                          {run.status.replace("_", " ")}
                        </PBBadge>
                      </div>
                      <p className="text-xs text-bronze-dark/40 flex items-center gap-1.5">
                        <Clock className="w-3 h-3" />
                        Submitted: {new Date(run.submitted_at).toLocaleString()}
                      </p>
                    </div>

                    <div className="flex gap-2">
                      <PBButton variant="secondary" size="sm">
                        View Report
                      </PBButton>
                      <PBButton 
                        variant="primary" 
                        size="sm" 
                        className="bg-success hover:bg-success/90 text-white"
                        onClick={() => handleDecide(run.run_id, "approved")}
                        disabled={actionLoading === run.run_id}
                      >
                        {actionLoading === run.run_id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Approve"}
                      </PBButton>
                      <PBButton 
                        variant="danger" 
                        size="sm"
                        onClick={() => handleDecide(run.run_id, "rejected")}
                        disabled={actionLoading === run.run_id}
                      >
                        {actionLoading === run.run_id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Reject"}
                      </PBButton>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* ── Recent Decisions ── */}
          <div className="space-y-4">
            <h2 className="type-h3">Recent Decisions</h2>
            <div className="surface-card divide-y divide-border-subtle">
              {queueData.recent_decisions.map((decision: any, idx: number) => (
                <div key={idx} className="p-4 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-charcoal">{decision.run_id}</p>
                    <p className="text-xs text-bronze-dark/40">
                      {new Date(decision.decided_at).toLocaleTimeString()}
                    </p>
                  </div>
                  {decision.decision === "APPROVED" ? (
                    <span className="flex items-center gap-1 text-xs text-success font-semibold">
                      <CheckCircle className="w-3.5 h-3.5" /> Approved
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-xs text-danger font-semibold">
                      <XCircle className="w-3.5 h-3.5" /> Rejected
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
