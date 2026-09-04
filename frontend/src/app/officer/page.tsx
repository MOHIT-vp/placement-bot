"use client";

import { useEffect, useState } from "react";
import { getOfficerQueue, getSystemStats } from "@/lib/api";
import { Users, CheckCircle, XCircle, Clock, ShieldAlert, BarChart3 } from "lucide-react";
import Link from "next/link";

export default function OfficerDashboardPage() {
  const [queueData, setQueueData] = useState<any>(null);
  const [statsData, setStatsData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [queue, stats] = await Promise.all([getOfficerQueue(), getSystemStats()]);
        setQueueData(queue);
        setStatsData(stats);
      } catch (err) {
        console.warn("Backend unavailable, loading demo data...");
        // Fallback demo data for frontend testing
        setTimeout(() => {
          setQueueData({
            officer_role: "PLACEMENT_CONVENOR",
            pending_runs: [
              { run_id: "RUN-101", student_id: "STU-01", submitted_at: new Date(Date.now() - 3600000).toISOString(), status: "AWAITING_REVIEW" },
              { run_id: "RUN-102", student_id: "STU-05", submitted_at: new Date(Date.now() - 7200000).toISOString(), status: "AWAITING_REVIEW" },
              { run_id: "RUN-103", student_id: "STU-08", submitted_at: new Date(Date.now() - 86400000).toISOString(), status: "AWAITING_REVIEW" }
            ],
            recent_decisions: [
              { run_id: "RUN-099", decision: "APPROVED", decided_at: new Date().toISOString() },
              { run_id: "RUN-098", decision: "REJECTED", decided_at: new Date(Date.now() - 500000).toISOString() }
            ]
          });
          setStatsData({
            total_runs: 145,
            pending_reviews: 3,
            approval_rate_percent: 88.5,
            published_versions: 120
          });
          setLoading(false);
        }, 1000);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center dark bg-background">
        <div className="flex flex-col items-center">
          <div className="w-16 h-16 border-4 border-purple-500/20 border-t-purple-500 rounded-full animate-spin"></div>
          <p className="mt-4 text-muted-foreground animate-pulse">Loading Placement Officer Queue...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen dark bg-background p-4 md:p-8">
      {/* Background Gradients */}
      <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none -z-10">
        <div className="absolute top-[-10%] right-[-10%] w-[40%] h-[40%] bg-pink-500/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[40%] h-[40%] bg-indigo-500/10 rounded-full blur-[120px]" />
      </div>

      <div className="max-w-7xl mx-auto space-y-8 animate-in fade-in duration-700">
        
        {/* Header */}
        <header className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-6 border-b border-white/10">
          <div>
            <div className="inline-flex items-center space-x-2 bg-purple-500/10 text-purple-400 text-xs font-medium px-2.5 py-1 rounded-full mb-3 border border-purple-500/20">
              <ShieldAlert className="w-3 h-3" />
              <span>Officer Console</span>
            </div>
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight">Review & Approval Queue</h1>
            <p className="text-muted-foreground mt-1">Manage student readiness evaluations before publication.</p>
          </div>
          <Link href="/" className="text-sm text-blue-400 hover:text-blue-300">Back to Portal</Link>
        </header>

        {/* System Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="glass-card flex flex-col p-5">
            <span className="text-sm text-muted-foreground mb-1 flex items-center"><BarChart3 className="w-4 h-4 mr-2" />Total Runs</span>
            <span className="text-3xl font-bold">{statsData.total_runs}</span>
          </div>
          <div className="glass-card flex flex-col p-5 border-t-2 border-t-yellow-500/50">
            <span className="text-sm text-muted-foreground mb-1 flex items-center"><Clock className="w-4 h-4 mr-2 text-yellow-400" />Pending Reviews</span>
            <span className="text-3xl font-bold text-yellow-400">{statsData.pending_reviews}</span>
          </div>
          <div className="glass-card flex flex-col p-5 border-t-2 border-t-green-500/50">
            <span className="text-sm text-muted-foreground mb-1 flex items-center"><CheckCircle className="w-4 h-4 mr-2 text-green-400" />Approval Rate</span>
            <span className="text-3xl font-bold text-green-400">{statsData.approval_rate_percent}%</span>
          </div>
          <div className="glass-card flex flex-col p-5">
            <span className="text-sm text-muted-foreground mb-1 flex items-center"><Users className="w-4 h-4 mr-2" />Published</span>
            <span className="text-3xl font-bold">{statsData.published_versions}</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
          
          {/* Pending Queue */}
          <div className="md:col-span-2 space-y-4">
            <h2 className="text-xl font-semibold mb-2">Pending Evaluations</h2>
            
            {queueData.pending_runs.length === 0 ? (
              <div className="glass-card text-center p-12 text-muted-foreground">
                No pending evaluations in the queue.
              </div>
            ) : (
              <div className="glass-card !p-0 overflow-hidden divide-y divide-white/10">
                {queueData.pending_runs.map((run: any) => (
                  <div key={run.run_id} className="p-4 flex flex-col sm:flex-row sm:items-center justify-between hover:bg-white/5 transition-colors group">
                    <div className="mb-4 sm:mb-0">
                      <div className="flex items-center space-x-3 mb-1">
                        <span className="font-semibold text-lg">{run.student_id}</span>
                        <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded-md border border-yellow-500/20">
                          {run.status}
                        </span>
                      </div>
                      <div className="text-sm text-muted-foreground flex items-center">
                        <Clock className="w-3 h-3 mr-1" />
                        Submitted: {new Date(run.submitted_at).toLocaleString()}
                      </div>
                    </div>
                    
                    <div className="flex space-x-2">
                      <button className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm font-medium transition-colors">
                        View Report
                      </button>
                      <button className="px-4 py-2 bg-green-600/20 hover:bg-green-600/40 text-green-400 border border-green-500/30 rounded-lg text-sm font-medium transition-colors">
                        Approve
                      </button>
                      <button className="px-4 py-2 bg-red-600/20 hover:bg-red-600/40 text-red-400 border border-red-500/30 rounded-lg text-sm font-medium transition-colors">
                        Reject
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Recent Decisions Sidebar */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold mb-2">Recent Decisions</h2>
            <div className="glass-card !p-0 overflow-hidden divide-y divide-white/10">
              {queueData.recent_decisions.map((decision: any, idx: number) => (
                <div key={idx} className="p-4 flex items-center justify-between bg-white/5">
                  <div>
                    <p className="text-sm font-medium text-white">{decision.run_id}</p>
                    <p className="text-xs text-muted-foreground">{new Date(decision.decided_at).toLocaleTimeString()}</p>
                  </div>
                  {decision.decision === "APPROVED" ? (
                    <span className="flex items-center text-xs text-green-400 font-medium">
                      <CheckCircle className="w-4 h-4 mr-1" /> Approved
                    </span>
                  ) : (
                    <span className="flex items-center text-xs text-red-400 font-medium">
                      <XCircle className="w-4 h-4 mr-1" /> Rejected
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
