/**
 * API client for RecruiterMind AI backend.
 * Handles communication with the FastAPI backend server.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export interface ApiError {
  detail: string;
  status_code: number;
}

export class ApiClientError extends Error {
  statusCode: number;
  details: any;

  constructor(message: string, statusCode: number, details?: any) {
    super(message);
    this.name = "ApiClientError";
    this.statusCode = statusCode;
    this.details = details;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorData: ApiError = { detail: `HTTP ${response.status}`, status_code: response.status };
    try {
      errorData = await response.json();
    } catch {}
    throw new ApiClientError(
      errorData.detail || `Request failed with status ${response.status}`,
      response.status,
      errorData
    );
  }
  return response.json();
}

function buildUrl(path: string, params?: Record<string, string | number | undefined>): string {
  const url = new URL(`${API_BASE_URL}${path}`);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.set(key, String(value));
      }
    });
  }
  return url.toString();
}

// ─── Job Description API ─────────────────────────────────────────────────────

export interface JobDescriptionInput {
  title: string;
  description: string;
}

export interface JobDescriptionSummary {
  id: number;
  title: string;
  created_at: string | null;
}

export interface JobDescriptionDetail {
  id: number;
  title: string;
  raw_text: string;
  required_skills: string[];
  optional_skills: string[];
  experience_min: number | null;
  experience_max: number | null;
  behavioral_traits: string[];
  created_at: string | null;
}

export async function uploadJobDescription(data: JobDescriptionInput): Promise<{ message: string; job_description_id: number; title: string }> {
  const response = await fetch(buildUrl("/upload-jd/"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse(response);
}

export async function listJobDescriptions(skip = 0, limit = 100): Promise<JobDescriptionSummary[]> {
  const response = await fetch(buildUrl("/upload-jd/", { skip, limit }));
  return handleResponse(response);
}

export async function getJobDescription(id: number): Promise<JobDescriptionDetail> {
  const response = await fetch(buildUrl(`/upload-jd/${id}`));
  return handleResponse(response);
}

export async function deleteJobDescription(id: number): Promise<{ message: string; job_description_id: number }> {
  const response = await fetch(buildUrl(`/upload-jd/${id}`), { method: "DELETE" });
  return handleResponse(response);
}

// ─── Candidate API ───────────────────────────────────────────────────────────

export interface CandidateInput {
  name: string;
  profile_text: string;
}

export interface CandidateSummary {
  id: number;
  name: string;
  experience_years: number | null;
  skills: string[] | null;
  created_at: string | null;
}

export interface CandidateDetail {
  id: number;
  name: string;
  raw_profile: string;
  profile_json: any;
  skills: string[] | null;
  experience_years: number | null;
  languages: string[] | null;
  education: string | null;
  certifications: string[] | null;
  projects: any[] | null;
  summary: string | null;
  created_at: string | null;
}

export async function uploadCandidate(data: CandidateInput): Promise<{ message: string; candidates: { id: number; name: string }[] }> {
  const response = await fetch(buildUrl("/upload-candidates/"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify([data]),
  });
  return handleResponse(response);
}

export async function uploadCandidates(data: CandidateInput[]): Promise<{ message: string; candidates: { id: number; name: string }[] }> {
  const response = await fetch(buildUrl("/upload-candidates/"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse(response);
}

export async function listCandidates(skip = 0, limit = 100): Promise<CandidateSummary[]> {
  const response = await fetch(buildUrl("/upload-candidates/", { skip, limit }));
  return handleResponse(response);
}

export async function getCandidate(id: number): Promise<CandidateDetail> {
  const response = await fetch(buildUrl(`/upload-candidates/${id}`));
  return handleResponse(response);
}

export async function deleteCandidate(id: number): Promise<{ message: string; candidate_id: number }> {
  const response = await fetch(buildUrl(`/upload-candidates/${id}`), { method: "DELETE" });
  return handleResponse(response);
}

// ─── Analysis API ────────────────────────────────────────────────────────────

export interface AnalysisRequest {
  job_description_id: number;
  candidate_ids?: number[];  // Optional - if not provided, system ranks all candidates
}

export interface AnalysisResult {
  analysis_id: string;
  job_title: string;
  total_candidates_analyzed: number;
  total_ranked: number;
  twin_groups_found: number;
  candidates_in_twin_groups: number;
  rankings: RankedCandidate[];
  twin_analysis: Record<string, any>;
}

export interface RankedCandidate {
  rank: number;
  candidate_id: number;
  name: string;
  overall_score: number;
  component_scores: {
    technical_relevance: number;
    behavioral_signals: number;
    learning_agility: number;
    stability: number;
    career_growth: number;
    risk_indicators: number;
    similarity_score: number;
  };
  reasoning: {
    strengths: string[];
    weaknesses: string[];
    why_shortlisted: string;
    risk_level: string;
  };
  prediction: {
    success_probability: number;
    month_1: string;
    month_3: string;
    month_6: string;
    reasoning: Record<string, string>;
  };
  twin_group_id: string | null;
  is_strongest_in_twin_group: boolean | null;
}

export async function runAnalysis(request: AnalysisRequest): Promise<AnalysisResult> {
  const response = await fetch(buildUrl("/analyze/"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  return handleResponse(response);
}

// ─── Rankings API ────────────────────────────────────────────────────────────

export interface RankingEntry {
  rank: number;
  candidate_id: number;
  job_description_id: number;
  overall_score: number;
  technical_fit_score: number;
  behavioral_fit_score: number;
  learning_agility_score: number;
  stability_score: number;
  growth_potential_score: number;
  explanations: Record<string, any> | null;
  created_at: string | null;
}

export async function getRankings(jobDescriptionId: number, skip = 0, limit = 100): Promise<RankingEntry[]> {
  const response = await fetch(buildUrl("/rankings/", { job_description_id: jobDescriptionId, skip, limit }));
  return handleResponse(response);
}

export async function getCandidateRanking(candidateId: number, jobDescriptionId: number): Promise<RankingEntry> {
  const response = await fetch(buildUrl(`/rankings/${candidateId}`, { job_description_id: jobDescriptionId }));
  return handleResponse(response);
}

// ─── Prediction API ──────────────────────────────────────────────────────────

export interface PredictionResult {
  id: number;
  candidate_id: number;
  job_description_id: number;
  success_probability: number;
  month_1_performance: string | null;
  month_3_performance: string | null;
  month_6_performance: string | null;
  reasoning: Record<string, string> | null;
  created_at: string | null;
}

export async function getPrediction(candidateId: number, jobDescriptionId?: number): Promise<PredictionResult> {
  const response = await fetch(buildUrl(`/prediction/${candidateId}`, jobDescriptionId !== undefined ? { job_description_id: jobDescriptionId } : undefined));
  return handleResponse(response);
}

export async function getJobPredictions(jobDescriptionId: number, skip = 0, limit = 100): Promise<PredictionResult[]> {
  const response = await fetch(buildUrl(`/prediction/job/${jobDescriptionId}`, { skip, limit }));
  return handleResponse(response);
}

// ─── Interview Questions API ─────────────────────────────────────────────────

export interface InterviewQuestions {
  technical_questions: string[];
  behavioral_questions: string[];
  leadership_questions: string[];
  risk_validation_questions: string[];
}

export async function getInterviewQuestions(candidateId: number, jobDescriptionId: number): Promise<InterviewQuestions> {
  const response = await fetch(buildUrl(`/interview-questions/${candidateId}`, { job_description_id: jobDescriptionId }));
  return handleResponse(response);
}

// ─── Health Check ────────────────────────────────────────────────────────────

export async function healthCheck(): Promise<{ service: string; version: string; status: string }> {
  const response = await fetch(buildUrl("/"));
  return handleResponse(response);
}

export default {
  uploadJobDescription,
  listJobDescriptions,
  getJobDescription,
  uploadCandidate,
  uploadCandidates,
  listCandidates,
  getCandidate,
  runAnalysis,
  getRankings,
  getCandidateRanking,
  getPrediction,
  getJobPredictions,
  getInterviewQuestions,
  healthCheck,
};