import type { Project } from '@/types/project';

export const DEFAULT_PROJECT_ID = 'default';

const PROJECTS_KEY = 'externalhound.projects';
const CURRENT_PROJECT_KEY = 'externalhound.currentProjectId';

const getStorage = (): Storage | null => {
  if (typeof window === 'undefined') return null;
  return window.localStorage;
};

const defaultProjects = (): Project[] => [{ id: DEFAULT_PROJECT_ID }];

const sanitizeProjects = (projects: unknown): Project[] => {
  if (!Array.isArray(projects)) return defaultProjects();
  const seen = new Set<string>();
  const sanitized: Project[] = [];
  projects.forEach((entry) => {
    if (!entry || typeof entry !== 'object') return;
    const record = entry as Project;
    const rawId = typeof record.id === 'string' ? record.id.trim() : '';
    const id = rawId ? rawId.toLowerCase() : '';
    if (!id || !isValidProjectId(id) || seen.has(id)) return;
    const name = typeof record.name === 'string' ? record.name.trim() : '';
    sanitized.push(name ? { id, name } : { id });
    seen.add(id);
  });
  return sanitized.length ? sanitized : defaultProjects();
};

export const loadProjects = (): Project[] => {
  const storage = getStorage();
  if (!storage) return defaultProjects();
  const raw = storage.getItem(PROJECTS_KEY);
  if (!raw) return defaultProjects();
  try {
    return sanitizeProjects(JSON.parse(raw));
  } catch {
    return defaultProjects();
  }
};

export const saveProjects = (projects: Project[]): void => {
  const storage = getStorage();
  if (!storage) return;
  storage.setItem(PROJECTS_KEY, JSON.stringify(projects));
};

export const loadCurrentProjectId = (projects: Project[]): string => {
  const storage = getStorage();
  const fallback = projects[0]?.id ?? DEFAULT_PROJECT_ID;
  if (!storage) return fallback;
  const stored = storage.getItem(CURRENT_PROJECT_KEY);
  if (stored && projects.some((project) => project.id === stored)) {
    return stored;
  }
  storage.setItem(CURRENT_PROJECT_KEY, fallback);
  return fallback;
};

export const saveCurrentProjectId = (projectId: string): void => {
  const storage = getStorage();
  if (!storage) return;
  storage.setItem(CURRENT_PROJECT_KEY, projectId);
};

export const getCurrentProjectId = (): string => {
  const projects = loadProjects();
  return loadCurrentProjectId(projects);
};

export const normalizeProjectId = (value: string): string => {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
};

export const isValidProjectId = (value: string): boolean => {
  return /^[a-z0-9][a-z0-9_-]*$/.test(value);
};
