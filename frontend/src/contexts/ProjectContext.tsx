import type { ReactNode } from 'react';
import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import type { Project } from '@/types/project';
import { DEFAULT_PROJECT_ID } from '@/utils/projects';
import {
  loadCurrentProjectId,
  loadProjects,
  saveCurrentProjectId,
  saveProjects,
} from '@/utils/projects';

type ProjectContextValue = {
  projects: Project[];
  currentProjectId: string;
  setCurrentProjectId: (projectId: string) => void;
  addProject: (project: Project) => void;
  removeProject: (projectId: string) => void;
};

const ProjectContext = createContext<ProjectContextValue | undefined>(undefined);

export const ProjectProvider = ({ children }: { children: ReactNode }) => {
  const initialProjects = loadProjects();
  const [projects, setProjects] = useState<Project[]>(() => initialProjects);
  const [currentProjectId, setCurrentProjectIdState] = useState<string>(() =>
    loadCurrentProjectId(initialProjects),
  );
  const queryClient = useQueryClient();
  const previousProjectId = useRef(currentProjectId);

  const setCurrentProjectId = useCallback((projectId: string) => {
    setCurrentProjectIdState(projectId);
    saveCurrentProjectId(projectId);
  }, []);

  const addProject = useCallback(
    (project: Project) => {
      setProjects((prev) => {
        const exists = prev.some((item) => item.id === project.id);
        const next = exists
          ? prev.map((item) => (item.id === project.id ? project : item))
          : [...prev, project];
        saveProjects(next);
        return next;
      });
      setCurrentProjectId(project.id);
    },
    [setCurrentProjectId],
  );

  const removeProject = useCallback(
    (projectId: string) => {
      setProjects((prev) => {
        const next = prev.filter((item) => item.id !== projectId);
        const normalized = next.length ? next : [{ id: DEFAULT_PROJECT_ID }];
        saveProjects(normalized);
        if (projectId === currentProjectId) {
          const fallback =
            normalized.find((item) => item.id === DEFAULT_PROJECT_ID) || normalized[0];
          setCurrentProjectIdState(fallback.id);
          saveCurrentProjectId(fallback.id);
        }
        return normalized;
      });
    },
    [currentProjectId],
  );

  useEffect(() => {
    if (previousProjectId.current !== currentProjectId) {
      const previousId = previousProjectId.current;
      queryClient.removeQueries({
        predicate: (query) =>
          Array.isArray(query.queryKey) &&
          query.queryKey[0] === 'project' &&
          query.queryKey[1] === previousId,
      });
      previousProjectId.current = currentProjectId;
    }
  }, [currentProjectId, queryClient]);

  const value = {
    projects,
    currentProjectId,
    setCurrentProjectId,
    addProject,
    removeProject,
  };

  return <ProjectContext.Provider value={value}>{children}</ProjectContext.Provider>;
};

export const useProject = (): ProjectContextValue => {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error('useProject must be used within ProjectProvider');
  }
  return context;
};
