// Mock data for RecruiterMind AI
export type Candidate = {
  id: string;
  name: string;
  role: string;
  experience: number;
  location: string;
  avatar: string;
  overall: number;
  technical: number;
  behavioral: number;
  growth: number;
  agility: number;
  stability: number;
  leadership: number;
  communication: number;
  risk: "Low" | "Medium" | "High";
  skills: string[];
  education: string;
  summary: string;
  strengths: string[];
  risks: string[];
  certifications: string[];
  projects: { name: string; description: string; year: string }[];
  timeline: { year: string; role: string; company: string }[];
};

const initials = (n: string) => n.split(" ").map(x => x[0]).join("").slice(0,2);
const avatar = (n: string, hue: number) =>
  `https://api.dicebear.com/9.x/initials/svg?seed=${encodeURIComponent(n)}&backgroundColor=${hue.toString(16).padStart(2,'0')}336d,7c3aed&backgroundType=gradientLinear&textColor=ffffff`;

export const candidates: Candidate[] = [
  {
    id: "c1", name: "Aria Chen", role: "Senior ML Engineer", experience: 7, location: "San Francisco, CA",
    avatar: avatar("Aria Chen", 40), overall: 96, technical: 97, behavioral: 92, growth: 95, agility: 94, stability: 88, leadership: 84, communication: 91,
    risk: "Low",
    skills: ["PyTorch","LLMs","Distributed Training","Python","Kubernetes","MLOps"],
    education: "MS Stanford — Computer Science",
    summary: "Aria pairs deep ML systems expertise with a strong product instinct. Track record of shipping foundation-model features at scale and mentoring junior engineers.",
    strengths: ["Owns ambiguous problems end-to-end","Production LLM deployment experience","Mentors and uplifts team"],
    risks: ["Limited people-management scope"],
    certifications: ["AWS ML Specialty","Kubernetes CKA"],
    projects: [
      { name: "Realtime Ranking Platform", description: "Built a sub-100ms ranking service handling 2B requests/day", year: "2024" },
      { name: "LLM Cost Optimizer", description: "Reduced inference cost by 64% via distillation + quantization", year: "2023" },
    ],
    timeline: [
      { year: "2022–Now", role: "Staff ML Engineer", company: "Northwind AI" },
      { year: "2019–2022", role: "Senior ML Engineer", company: "Lumen Labs" },
      { year: "2017–2019", role: "ML Engineer", company: "Quanta" },
    ],
  },
  {
    id: "c2", name: "Marcus Patel", role: "Staff Backend Engineer", experience: 9, location: "Austin, TX",
    avatar: avatar("Marcus Patel", 50), overall: 93, technical: 95, behavioral: 89, growth: 87, agility: 90, stability: 94, leadership: 88, communication: 86,
    risk: "Low",
    skills: ["Go","Postgres","Kafka","gRPC","AWS","System Design"],
    education: "BS UT Austin — CS",
    summary: "Marcus has architected high-throughput payment infrastructure at three companies and leads with quiet rigor.",
    strengths: ["Distributed systems depth","Calm under pressure","Excellent code reviewer"],
    risks: ["Less exposure to ML-heavy roadmaps"],
    certifications: ["AWS Solutions Architect Pro"],
    projects: [
      { name: "Ledger v2", description: "Redesigned core ledger to support 50M TPS with strong consistency", year: "2023" },
    ],
    timeline: [
      { year: "2021–Now", role: "Staff Engineer", company: "Vault Pay" },
      { year: "2018–2021", role: "Senior Engineer", company: "Stripeline" },
    ],
  },
  {
    id: "c3", name: "Sofia Reyes", role: "Product Designer", experience: 6, location: "Remote · Mexico City",
    avatar: avatar("Sofia Reyes", 60), overall: 91, technical: 84, behavioral: 95, growth: 93, agility: 96, stability: 86, leadership: 80, communication: 96,
    risk: "Low",
    skills: ["Figma","Design Systems","Prototyping","User Research","Motion"],
    education: "BFA Parsons — Design",
    summary: "Sofia drives 0→1 product design with rare clarity. Strong systems thinker with a portfolio of shipped enterprise UX.",
    strengths: ["Exceptional craft","Cross-functional partner","Rapid prototyping"],
    risks: ["Smaller team backgrounds — scale TBD"],
    certifications: ["NN/g UX Master"],
    projects: [{ name: "Atlas Design System", description: "Unified 12 product surfaces under one accessible system", year: "2024" }],
    timeline: [
      { year: "2022–Now", role: "Senior Designer", company: "Helix" },
      { year: "2019–2022", role: "Product Designer", company: "Crate" },
    ],
  },
  {
    id: "c4", name: "Jonas Berg", role: "Engineering Manager", experience: 11, location: "Berlin, DE",
    avatar: avatar("Jonas Berg", 70), overall: 89, technical: 80, behavioral: 92, growth: 84, agility: 82, stability: 95, leadership: 96, communication: 93,
    risk: "Low",
    skills: ["Leadership","Hiring","Roadmapping","Coaching","Architecture"],
    education: "MS TU Munich",
    summary: "Jonas has scaled platform orgs from 8 to 60 with low attrition and high delivery velocity.",
    strengths: ["Hiring excellence","Long-tenured reports","Strong written communication"],
    risks: ["Hands-on coding limited recently"],
    certifications: ["ICF Leadership Coach"],
    projects: [{ name: "Platform Org Rebuild", description: "Restructured platform org reducing on-call load 40%", year: "2024" }],
    timeline: [
      { year: "2020–Now", role: "Director of Engineering", company: "Nordic Cloud" },
      { year: "2016–2020", role: "EM", company: "Foundry" },
    ],
  },
  {
    id: "c5", name: "Priya Nair", role: "Data Scientist", experience: 4, location: "Bangalore, IN",
    avatar: avatar("Priya Nair", 80), overall: 87, technical: 90, behavioral: 84, growth: 96, agility: 92, stability: 78, leadership: 70, communication: 88,
    risk: "Medium",
    skills: ["Python","Causal Inference","SQL","Experimentation","Tableau"],
    education: "MS IISc — Statistics",
    summary: "Priya is a high-velocity learner producing experimentation frameworks now used company-wide.",
    strengths: ["Rigorous statistical thinking","Self-directed learner"],
    risks: ["Earlier career — leadership exposure limited","2 short tenures"],
    certifications: ["Google Advanced Analytics"],
    projects: [{ name: "Causal Lift Framework", description: "Adopted across 6 product teams", year: "2024" }],
    timeline: [
      { year: "2023–Now", role: "Data Scientist II", company: "Plumeria" },
      { year: "2021–2023", role: "Data Scientist", company: "Karta" },
    ],
  },
  {
    id: "c6", name: "Liam O'Connor", role: "Frontend Engineer", experience: 5, location: "Dublin, IE",
    avatar: avatar("Liam O'Connor", 90), overall: 85, technical: 88, behavioral: 82, growth: 86, agility: 88, stability: 84, leadership: 72, communication: 84,
    risk: "Low",
    skills: ["React","TypeScript","Performance","WebGL","Design Systems"],
    education: "BS Trinity College Dublin",
    summary: "Liam ships pixel-perfect UI with strong attention to performance and accessibility.",
    strengths: ["UI craft","Performance instincts"],
    risks: ["Less backend exposure"],
    certifications: [],
    projects: [{ name: "Editor Rewrite", description: "Cut TTI by 58% on flagship editor", year: "2024" }],
    timeline: [{ year: "2022–Now", role: "Senior FE", company: "Loop" }],
  },
  {
    id: "c7", name: "Yuki Tanaka", role: "Security Engineer", experience: 8, location: "Tokyo, JP",
    avatar: avatar("Yuki Tanaka", 100), overall: 84, technical: 92, behavioral: 80, growth: 78, agility: 76, stability: 92, leadership: 78, communication: 76,
    risk: "Medium",
    skills: ["AppSec","Threat Modeling","Cryptography","Cloud Security"],
    education: "MS U Tokyo",
    summary: "Yuki brings deep AppSec expertise and a methodical approach to risk reduction.",
    strengths: ["Deep security expertise","Methodical"],
    risks: ["Communication across non-security teams"],
    certifications: ["OSCP","CISSP"],
    projects: [{ name: "Zero-trust rollout", description: "Implemented org-wide zero-trust mesh", year: "2023" }],
    timeline: [{ year: "2019–Now", role: "Senior Sec Eng", company: "Sakura Cloud" }],
  },
  {
    id: "c8", name: "Elena Rossi", role: "Senior Product Manager", experience: 8, location: "London, UK",
    avatar: avatar("Elena Rossi", 110), overall: 82, technical: 70, behavioral: 90, growth: 84, agility: 86, stability: 88, leadership: 86, communication: 94,
    risk: "Low",
    skills: ["Product Strategy","User Research","Roadmapping","Analytics"],
    education: "MBA LBS",
    summary: "Elena bridges customer insight with sharp prioritization. Shipped two flagship enterprise features.",
    strengths: ["Customer empathy","Excellent communicator"],
    risks: ["Less technical depth on infra products"],
    certifications: ["Pragmatic PM"],
    projects: [{ name: "Enterprise SSO", description: "Drove product strategy for enterprise auth suite", year: "2024" }],
    timeline: [{ year: "2021–Now", role: "Senior PM", company: "Mercato" }],
  },
];

export const stats = {
  totalCandidates: 12847,
  activeJobs: 38,
  shortlisted: 264,
  matchAccuracy: 94.2,
  hiringSuccess: 88.6,
};

export const candidateDistribution = [
  { name: "Engineering", value: 4820 },
  { name: "Design", value: 1240 },
  { name: "Product", value: 1890 },
  { name: "Data", value: 2160 },
  { name: "Security", value: 980 },
  { name: "Leadership", value: 1757 },
];

export const skillTrends = [
  { month: "Jan", ml: 62, infra: 70, frontend: 68 },
  { month: "Feb", ml: 66, infra: 72, frontend: 70 },
  { month: "Mar", ml: 71, infra: 74, frontend: 71 },
  { month: "Apr", ml: 75, infra: 76, frontend: 73 },
  { month: "May", ml: 81, infra: 78, frontend: 75 },
  { month: "Jun", ml: 86, infra: 80, frontend: 77 },
  { month: "Jul", ml: 90, infra: 83, frontend: 80 },
];

export const funnel = [
  { stage: "Applied", count: 12847 },
  { stage: "AI Screened", count: 4120 },
  { stage: "Shortlisted", count: 864 },
  { stage: "Interviewed", count: 286 },
  { stage: "Offered", count: 92 },
  { stage: "Hired", count: 68 },
];

export const accuracyTrend = [
  { week: "W1", accuracy: 86 },
  { week: "W2", accuracy: 88 },
  { week: "W3", accuracy: 90 },
  { week: "W4", accuracy: 91 },
  { week: "W5", accuracy: 92.5 },
  { week: "W6", accuracy: 93.4 },
  { week: "W7", accuracy: 94.2 },
];

export const activity = [
  { who: "Aria Chen", what: "moved to Final Interview", when: "2m ago" },
  { who: "Marcus Patel", what: "shortlisted for Staff Backend", when: "14m ago" },
  { who: "Sofia Reyes", what: "AI insight generated", when: "32m ago" },
  { who: "Priya Nair", what: "uploaded updated resume", when: "1h ago" },
  { who: "Liam O'Connor", what: "scored 85 on Frontend role", when: "2h ago" },
];

export const jdExtraction = {
  required: [
    { skill: "Python", confidence: 98 },
    { skill: "Distributed Systems", confidence: 94 },
    { skill: "PyTorch / TensorFlow", confidence: 91 },
    { skill: "Kubernetes", confidence: 87 },
  ],
  nice: [
    { skill: "Rust", confidence: 72 },
    { skill: "GPU optimization (CUDA)", confidence: 68 },
    { skill: "Open-source contributions", confidence: 64 },
  ],
  experience: "6–10 years, with 2+ years in production ML",
  behavioral: ["Ownership","Bias for action","Customer obsession","Cross-functional partnership"],
  leadership: "Technical leadership of 3–6 engineers; mentorship; roadmap influence",
};

export const interviewQuestions = {
  technical: [
    "Walk us through the most complex distributed system you've designed. What were the tradeoffs?",
    "How would you architect a low-latency feature store for an LLM ranking pipeline?",
    "Explain a time you debugged a non-obvious performance regression in production.",
  ],
  behavioral: [
    "Describe a project where requirements changed mid-flight. How did you adapt?",
    "Tell me about a time you disagreed with your manager. How did it resolve?",
    "What's the most useful piece of feedback you've received?",
  ],
  leadership: [
    "How do you uplift the engineers around you?",
    "Describe how you'd onboard a new senior hire into your team.",
    "Tell us about a difficult performance conversation you led.",
  ],
  risk: [
    "Two short tenures in 2021–2023 — walk us through that period.",
    "You've less exposure to people management. How would you grow into the role?",
    "How do you handle ambiguous priorities from multiple stakeholders?",
  ],
};

export const prediction = {
  probability: 92,
  timeline: [
    { period: "Day 1", score: 70, label: "Onboarding" },
    { period: "Month 1", score: 78, label: "Ramping" },
    { period: "Month 3", score: 86, label: "Contributing" },
    { period: "Month 6", score: 92, label: "Owning" },
    { period: "Year 1", score: 96, label: "Driving outcomes" },
  ],
  strengths: ["Fast learner","Strong ownership","Relevant domain experience","Mentorship track record"],
  risks: ["Limited leadership exposure at scale"],
};

export const analytics = {
  quality: [
    { month: "Jan", score: 78 }, { month: "Feb", score: 80 }, { month: "Mar", score: 82 },
    { month: "Apr", score: 85 }, { month: "May", score: 87 }, { month: "Jun", score: 90 }, { month: "Jul", score: 92 },
  ],
  skillGap: [
    { skill: "LLMs", have: 62, need: 90 },
    { skill: "Infra", have: 78, need: 85 },
    { skill: "Design", have: 70, need: 80 },
    { skill: "Security", have: 55, need: 75 },
    { skill: "Leadership", have: 60, need: 80 },
  ],
};
