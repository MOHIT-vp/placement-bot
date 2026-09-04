"use client";

import { useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  UploadCloud, CheckCircle2, ChevronRight, Code2,
  GitBranch, AlertCircle, FileText, X, Loader2,
} from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
type ValidationState = "idle" | "checking" | "valid" | "invalid";

export default function OnboardingPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [step, setStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [progress, setProgress] = useState("");

  // Step 1
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [resumeError, setResumeError] = useState("");
  const [isDragging, setIsDragging] = useState(false);

  // Step 2
  const [leetcode, setLeetcode] = useState("");
  const [github, setGithub] = useState("");
  const [githubState, setGithubState] = useState<ValidationState>("idle");
  const [githubError, setGithubError] = useState("");
  const [githubUser, setGithubUser] = useState<{ login: string; avatar_url: string; public_repos: number } | null>(null);
  const [codingSolved, setCodingSolved] = useState("");
  const [cgpa, setCgpa] = useState("");
  const [consent, setConsent] = useState(false);

  const ALLOWED = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  ];

  function validateFile(f: File) {
    if (!ALLOWED.includes(f.type)) return "Only PDF or DOCX files accepted.";
    if (f.size > 5 * 1024 * 1024) return "File must be under 5 MB.";
    return "";
  }

  function handleFileSelect(f: File) {
    const err = validateFile(f);
    if (err) { setResumeError(err); setResumeFile(null); return; }
    setResumeError("");
    setResumeFile(f);
  }

  const onDragOver = useCallback((e: React.DragEvent) => { e.preventDefault(); setIsDragging(true); }, []);
  const onDragLeave = useCallback(() => setIsDragging(false), []);
  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setIsDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFileSelect(f);
  }, []);

  function handleContinue() {
    if (!resumeFile) { setResumeError("You must upload a resume before continuing."); return; }
    setStep(2);
  }

  async function validateGitHub(username: string) {
    if (!username.trim()) { setGithubState("idle"); setGithubUser(null); return; }
    setGithubState("checking"); setGithubError(""); setGithubUser(null);
    try {
      const res = await fetch(`https://api.github.com/users/${encodeURIComponent(username.trim())}`);
      if (res.status === 404) { setGithubState("invalid"); setGithubError(`GitHub user "${username}" does not exist.`); return; }
      if (!res.ok) { setGithubState("invalid"); setGithubError("GitHub API error, try again."); return; }
      const d = await res.json();
      setGithubUser({ login: d.login, avatar_url: d.avatar_url, public_repos: d.public_repos });
      setGithubState("valid");
    } catch { setGithubState("invalid"); setGithubError("Network error checking GitHub."); }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitError("");
    if (!resumeFile) { setSubmitError("Resume is required."); return; }
    if (github.trim() && githubState !== "valid") { setSubmitError("Verify GitHub username first."); return; }

    setIsSubmitting(true);
    setProgress("Uploading resume...");

    try {
      const form = new FormData();
      form.append("file", resumeFile);
      if (leetcode.trim()) form.append("leetcode_handle", leetcode.trim());
      if (github.trim()) form.append("github_username", github.trim());
      if (codingSolved) form.append("coding_solved", codingSolved);
      if (cgpa) form.append("cgpa", cgpa);

      setProgress("AI agents analysing your resume...");
      const res = await fetch(`${API_BASE_URL}/api/v1/process/upload`, {
        method: "POST",
        body: form,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Server error ${res.status}`);
      }

      setProgress("Computing company matches...");
      const data = await res.json();

      // Store in localStorage so dashboard can read it
      localStorage.setItem("placement_result", JSON.stringify(data));

      setProgress("Redirecting to dashboard...");
      router.push("/dashboard");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unexpected error.";
      setSubmitError(msg);
      setIsSubmitting(false);
      setProgress("");
    }
  }

  function GithubIcon() {
    if (githubState === "checking") return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
    if (githubState === "valid") return <CheckCircle2 className="w-5 h-5 text-green-500" />;
    if (githubState === "invalid") return <AlertCircle className="w-5 h-5 text-red-500" />;
    return <GitBranch className="w-5 h-5 text-slate-400" />;
  }

  const canSubmit = consent && !!resumeFile && (githubState === "valid" || !github.trim()) && !isSubmitting;

  return (
    <div className="min-h-screen flex flex-col justify-center items-center p-8 bg-slate-50 text-slate-800">
      <div className="w-full max-w-2xl animate-in fade-in zoom-in-95 duration-500 z-10">

        {/* Progress steps */}
        <div className="flex items-center justify-between mb-8 px-4 relative">
          <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-1 bg-slate-200 rounded-full -z-10" />
          <div className="absolute left-0 top-1/2 -translate-y-1/2 h-1 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full transition-all duration-500 -z-10"
            style={{ width: step === 1 ? "50%" : "100%" }} />
          {[1, 2].map(n => (
            <div key={n} className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm transition-colors
              ${step >= n ? "bg-blue-600 text-white shadow-md" : "bg-white border border-slate-300 text-slate-400"}`}>
              {n}
            </div>
          ))}
        </div>

        <div className="bg-white p-8 rounded-2xl shadow-xl border border-slate-200 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500" />

          {/* Step 1: Resume */}
          {step === 1 && (
            <div className="space-y-6">
              <div className="text-center">
                <h2 className="text-3xl font-bold">Upload Resume</h2>
                <p className="text-slate-500 mt-1">The AI agent will extract your skills and experience.</p>
              </div>

              <input ref={fileInputRef} type="file" className="hidden"
                accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                onChange={e => { const f = e.target.files?.[0]; if (f) handleFileSelect(f); }} />

              {!resumeFile ? (
                <div onClick={() => fileInputRef.current?.click()}
                  onDragOver={onDragOver} onDragLeave={onDragLeave} onDrop={onDrop}
                  className={`border-2 border-dashed rounded-2xl p-12 text-center flex flex-col items-center cursor-pointer transition-all group
                    ${isDragging ? "border-blue-500 bg-blue-50 scale-[1.01]"
                      : resumeError ? "border-red-400 bg-red-50"
                      : "border-slate-300 hover:border-blue-400 hover:bg-slate-50"}`}>
                  <div className="p-4 bg-slate-100 rounded-full mb-4 group-hover:scale-110 transition-transform">
                    <UploadCloud className={`h-8 w-8 ${resumeError ? "text-red-500" : "text-blue-500"}`} />
                  </div>
                  <h3 className="font-semibold text-lg mb-1">Drag & Drop your resume</h3>
                  <p className="text-sm text-slate-500">PDF or DOCX · max 5 MB</p>
                  <div className="mt-5 px-6 py-2 bg-slate-100 rounded-full text-sm font-medium hover:bg-slate-200 transition-colors">
                    Browse Files
                  </div>
                </div>
              ) : (
                <div className="border border-green-300 bg-green-50 rounded-2xl p-5 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="p-3 bg-green-100 rounded-xl"><FileText className="w-6 h-6 text-green-600" /></div>
                    <div>
                      <p className="font-semibold truncate max-w-xs">{resumeFile.name}</p>
                      <p className="text-xs text-slate-500">{(resumeFile.size / 1024).toFixed(1)} KB</p>
                    </div>
                  </div>
                  <button onClick={e => { e.stopPropagation(); setResumeFile(null); setResumeError(""); }}
                    className="p-2 rounded-full hover:bg-green-200 transition-colors">
                    <X className="w-5 h-5 text-slate-500" />
                  </button>
                </div>
              )}

              {resumeError && (
                <div className="flex items-center gap-2 text-red-500 text-sm font-medium">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />{resumeError}
                </div>
              )}

              <button onClick={handleContinue}
                className="w-full flex items-center justify-center p-4 rounded-xl font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors shadow-sm">
                Continue <ChevronRight className="ml-2 w-5 h-5" />
              </button>
            </div>
          )}

          {/* Step 2: Profiles + extra info */}
          {step === 2 && (
            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="text-center">
                <h2 className="text-3xl font-bold">Your Details</h2>
                <p className="text-slate-500 mt-1">Provide additional info for accurate company matching.</p>
              </div>

              {/* LeetCode */}
              <div className="space-y-1.5">
                <label className="text-sm font-semibold text-slate-700">LeetCode Handle <span className="font-normal text-slate-400">(optional)</span></label>
                <div className="relative">
                  <Code2 className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <input type="text" placeholder="e.g. aditya123"
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl py-3 pl-10 pr-4 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all placeholder:text-slate-400"
                    value={leetcode} onChange={e => setLeetcode(e.target.value)} />
                </div>
              </div>

              {/* GitHub */}
              <div className="space-y-1.5">
                <label className="text-sm font-semibold text-slate-700">GitHub Username <span className="font-normal text-slate-400">(optional)</span></label>
                <div className="relative">
                  <div className="absolute left-3 top-1/2 -translate-y-1/2"><GithubIcon /></div>
                  <input type="text" placeholder="e.g. adityagithub"
                    className={`w-full bg-slate-50 border rounded-xl py-3 pl-10 pr-4 focus:outline-none focus:ring-1 transition-all placeholder:text-slate-400
                      ${githubState === "valid" ? "border-green-400 focus:ring-green-500/50"
                        : githubState === "invalid" ? "border-red-400 focus:ring-red-500/50"
                        : "border-slate-300 focus:border-indigo-500 focus:ring-indigo-500"}`}
                    value={github}
                    onChange={e => { setGithub(e.target.value); setGithubState("idle"); setGithubUser(null); }}
                    onBlur={() => { if (github.trim()) validateGitHub(github.trim()); }} />
                </div>
                {githubState === "invalid" && <div className="flex items-center gap-2 text-red-500 text-sm"><AlertCircle className="w-4 h-4" />{githubError}</div>}
                {githubState === "valid" && githubUser && (
                  <div className="flex items-center gap-3 p-3 bg-green-50 border border-green-200 rounded-xl">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={githubUser.avatar_url} alt={githubUser.login} className="w-8 h-8 rounded-full" />
                    <div>
                      <p className="text-sm font-bold text-green-700">@{githubUser.login}</p>
                      <p className="text-xs text-green-600">{githubUser.public_repos} public repos · Verified ✓</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Extra fields in a 2-col grid */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-sm font-semibold text-slate-700">Problems Solved <span className="font-normal text-slate-400">(LeetCode/HackerRank)</span></label>
                  <input type="number" min="0" max="5000" placeholder="e.g. 150"
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl py-3 px-4 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all placeholder:text-slate-400"
                    value={codingSolved} onChange={e => setCodingSolved(e.target.value)} />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-semibold text-slate-700">CGPA <span className="font-normal text-slate-400">(optional)</span></label>
                  <input type="number" step="0.01" min="0" max="10" placeholder="e.g. 8.5"
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl py-3 px-4 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all placeholder:text-slate-400"
                    value={cgpa} onChange={e => setCgpa(e.target.value)} />
                </div>
              </div>

              {/* Consent */}
              <div className="flex items-start gap-3 p-4 bg-slate-50 rounded-xl border border-slate-200">
                <input type="checkbox" id="consent" required checked={consent}
                  onChange={e => setConsent(e.target.checked)}
                  className="w-5 h-5 mt-0.5 rounded border-slate-300 text-blue-600 focus:ring-blue-500 cursor-pointer" />
                <div>
                  <label htmlFor="consent" className="text-sm font-bold cursor-pointer">I consent to data analysis</label>
                  <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                    I authorise the Placement Readiness Portal to analyse my resume and coding profiles. Data is processed locally and not stored in any database.
                  </p>
                </div>
              </div>

              {/* Submitting progress */}
              {isSubmitting && progress && (
                <div className="flex items-center gap-3 p-3 bg-blue-50 border border-blue-200 rounded-xl">
                  <Loader2 className="w-5 h-5 text-blue-600 animate-spin flex-shrink-0" />
                  <p className="text-sm font-medium text-blue-700">{progress}</p>
                </div>
              )}

              {submitError && (
                <div className="flex items-center gap-2 text-red-600 text-sm p-3 bg-red-50 rounded-xl border border-red-200 font-medium">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />{submitError}
                </div>
              )}

              <div className="flex gap-3 pt-1">
                <button type="button" onClick={() => setStep(1)}
                  className="w-1/3 p-4 rounded-xl font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 border border-slate-200 transition-colors">
                  Back
                </button>
                <button type="submit" disabled={!canSubmit}
                  className="w-2/3 flex items-center justify-center p-4 rounded-xl font-medium text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 shadow-md transition-all disabled:opacity-40 disabled:cursor-not-allowed">
                  {isSubmitting
                    ? <><Loader2 className="w-5 h-5 animate-spin mr-2" />Analysing...</>
                    : <><CheckCircle2 className="mr-2 w-5 h-5" />Analyse & View Dashboard</>}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
