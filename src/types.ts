export type Page =
  | 'dashboard'
  | 'analysis'
  | 'orchards'
  | 'reports'
  | 'calendar'
  | 'knowledge'
  | 'subscription'
  | 'admin'
export interface User {
  id: string
  name: string
  email: string | null
  role: string
  is_demo: number
  subscription_until: string | null
}
export interface Orchard {
  id: string
  name: string
  province: string
  city: string
  cultivar: string
  area: number
  trees: number
  irrigation: string
  age: number
  is_sample: number
}
export interface Task {
  id: string
  title: string
  kind: string
  due_date: string
  done: number
  orchard_id: string | null
  orchard_name: string | null
  is_sample: number
}
export interface Hypothesis {
  name: string
  confidence: number
  evidence: string
  next_step: string
}
export interface AnalysisData {
  title: string
  summary: string
  quality: string
  is_pistachio: boolean | null
  observations: string[]
  hypotheses: Hypothesis[]
  actions: string[]
  needed_tests: string[]
  follow_up_questions: string[]
  urgency: 'low' | 'medium' | 'high'
  knowledge_ids: string[]
  disclaimer: string
  provider: string
  knowledge_version: string
}
export interface Report {
  id: string
  orchard_id: string | null
  orchard_name: string | null
  tree_part: string
  notes: string
  data: AnalysisData
  image_url: string | null
  is_sample: number
  created_at: string
}
export interface Services {
  vision_configured: boolean
  vision_provider: string
  payment_configured: boolean
  payment_sandbox: boolean
  knowledge_version: string
  knowledge_reviewed: boolean
  weather_configured: boolean
}
export interface Plan {
  id: string
  name: string
  price_toman: number
  duration_days: number
  analyses_per_month: number
  features: string[]
}
export interface Bootstrap {
  user: User | null
  orchards: Orchard[]
  reports: Report[]
  tasks: Task[]
  usage: { used: number; limit: number; premium: boolean }
  services: Services
  plans: Plan[]
}
export interface Article {
  id: string
  title: string
  category: string
  category_label: string
  keywords: string
  image: string
  reading_minutes: number
  summary: string
  sections: { heading: string; body: string }[]
  sources: { title: string; url: string; scope: string }[]
  version: string
  updated_at: string
  review_status: string
  disclaimer: string
}
export interface Knowledge {
  articles: Article[]
  categories: { id: string; label: string }[]
  version: string
  notice: string
  reviewed: boolean
}
export interface Payment {
  id: string
  user_name?: string
  email?: string
  plan: string
  amount_rial: number
  status: string
  ref_id: string | null
  created_at: string
  authority?: string
  is_sandbox?: number
}
export interface AdminData {
  is_demo: boolean
  transactions: Payment[]
  users: {
    id: string
    name: string
    email: string
    role: string
    created_at: string
    subscription_until: string | null
    subscription_active?: boolean
    subscription_is_sandbox?: number
  }[]
  metrics: { revenue_rial: number; payments: number; pending: number; users: number }
  services: Services
}
export interface AppContext {
  data: Bootstrap
  knowledge: Knowledge
  refresh: () => Promise<void>
  navigate: (page: Page) => void
  notify: (message: string, type?: 'success' | 'error' | 'info') => void
  openArticle: (article: Article) => void
  openReport: (report: Report) => void
  openAuth: () => void
  openOrchard: (orchard?: Orchard) => void
  openTask: () => void
  startAnalysis: (file?: File, orchardId?: string) => void
}
