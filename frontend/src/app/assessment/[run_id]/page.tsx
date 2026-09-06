"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { Loader } from "@/components/ui/loader";
import { Clock, CheckCircle2, XCircle, ArrowRight, ExternalLink, Loader2 } from "lucide-react";
import { PBButton } from "@/components/ui/pb-button";
import { getWorkflowStatus } from "@/lib/api";
import Link from "next/link";

export default function AssessmentStatusPage() {
  const router = useRouter();
  const params = useParams();
  const runId = params.run_id as string;

  const [status, setStatus] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!runId) return;

    let intervalId: NodeJS.Timeout;

    const checkStatus = async () => {
      try {
        const response = await getWorkflowStatus(runId);
        
        setStatus(response.status);
        setCurrentStep(response.current_step || null);
        
        // Stop polling on terminal states
        if (response.status === "published" || response.status === "approved" || response.status === "rejected") {
          if (intervalId) clearInterval(intervalId);
        }
      } catch (err) {
        console.error("Error fetching assessment status:", err);
        setError("Failed to fetch assessment status.");
        if (intervalId) clearInterval(intervalId);
      }
    };

    // Initial check
    checkStatus();

    // Poll every 3 seconds if not in a terminal state
    intervalId = setInterval(() => {
      if (status !== "published" && status !== "rejected" && status !== "approved") {
        checkStatus();
      } else {
        clearInterval(intervalId);
      }
    }, 3000);

    return () => clearInterval(intervalId);
  }, [runId, status]);

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-ivory gap-4 p-8 text-center">
        <div className="w-16 h-16 rounded-full bg-danger-light/20 flex items-center justify-center">
          <XCircle className="w-8 h-8 text-danger" />
        </div>
        <h2 className="type-h3 text-charcoal">Error Checking Status</h2>
        <p className="text-sm text-bronze-dark/50">{error}</p>
        <PBButton onClick={() => router.push("/onboarding")} variant="secondary" className="mt-4">
          Return to Onboarding
        </PBButton>
      </div>
    );
  }

  if (!status || status === "running" || status === "init") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-ivory">
        <div className="flex flex-col items-center gap-6 mt-10 max-w-sm text-center">
          <Loader />
          <h2 className="type-h3 text-charcoal">Analyzing Profile</h2>
          <p className="text-sm text-bronze-dark/60">
            Your assessment is being prepared by our AI agents. This may take a moment.
            <br/><br/>
            <span className="font-medium text-bronze">Current Step:</span>{" "}
            <span className="font-semibold text-charcoal capitalize">
              {(currentStep || "Initializing").replace(/_/g, " ")}
            </span>
          </p>
        </div>
      </div>
    );
  }

  if (status === "pending_review" || status === "completed") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-ivory p-6">
        <div className="flex flex-col items-center gap-6 max-w-md text-center bg-surface p-12 rounded-3xl border border-border-subtle shadow-sm glass-panel">
          <div className="w-20 h-20 rounded-[20px] bg-warning-light flex items-center justify-center mb-2">
            <Clock className="w-10 h-10 text-warning" />
          </div>
          <h2 className="type-h2 text-charcoal">Assessment Complete</h2>
          <div className="space-y-4 text-left w-full bg-ivory p-6 rounded-2xl border border-border-subtle">
            <p className="text-sm text-bronze-dark/70 font-medium border-b border-border-subtle pb-3">Status Checklist</p>
            <ul className="space-y-3">
              <li className="flex items-center gap-3 text-sm text-charcoal font-medium">
                <CheckCircle2 className="w-5 h-5 text-success" /> AI analysis complete
              </li>
              <li className="flex items-center gap-3 text-sm text-charcoal font-medium">
                <CheckCircle2 className="w-5 h-5 text-success" /> Validation complete
              </li>
              <li className="flex items-center gap-3 text-sm text-warning font-medium">
                <Loader2 className="w-5 h-5 animate-spin" /> Placement Cell review pending
              </li>
            </ul>
          </div>
          <p className="text-sm text-bronze-dark/50 mt-2">
            Your AI-powered placement assessment has been generated and is currently awaiting review by the Placement Cell.
          </p>
          <div className="flex flex-col items-center w-full gap-4 mt-4">
            <PBButton onClick={() => window.location.reload()} variant="primary" className="w-full">
              Refresh Status
            </PBButton>
            
            <Link 
              href="/officer" 
              target="_blank" 
              className="text-xs text-bronze-dark/40 hover:text-primary transition-colors flex items-center gap-1 mt-4"
            >
              Demo: Open Placement Officer Console <ExternalLink className="w-3 h-3" />
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (status === "rejected") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-ivory">
        <div className="flex flex-col items-center gap-6 mt-10 max-w-sm text-center">
          <div className="w-20 h-20 rounded-[20px] bg-danger-light/20 flex items-center justify-center">
            <XCircle className="w-10 h-10 text-danger" />
          </div>
          <h2 className="type-h2 text-charcoal">Assessment Rejected</h2>
          <p className="text-sm text-bronze-dark/60">
            Your readiness assessment was reviewed and rejected by the Placement Officer. 
            Please contact the placement cell for more details.
          </p>
          <PBButton onClick={() => router.push("/onboarding")} variant="primary" className="mt-4">
            Start New Assessment
          </PBButton>
        </div>
      </div>
    );
  }

  if (status === "approved" || status === "published") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-ivory p-6">
        <div className="flex flex-col items-center gap-6 max-w-md text-center bg-surface p-12 rounded-3xl border border-border-subtle shadow-sm glass-panel">
          <div className="w-20 h-20 rounded-[20px] bg-success/10 flex items-center justify-center mb-2">
            <CheckCircle2 className="w-10 h-10 text-success" />
          </div>
          <h2 className="type-h2 text-charcoal">Assessment Approved</h2>
          <p className="text-sm text-bronze-dark/60">
            The Placement Cell has reviewed and approved your assessment. Your readiness dashboard is now available.
          </p>
          <PBButton onClick={() => router.push("/dashboard")} variant="primary" size="lg" className="mt-4 w-full">
            View My Placement Dashboard <ArrowRight className="w-4 h-4 ml-2" />
          </PBButton>
        </div>
      </div>
    );
  }

  // Fallback
  return null;
}
