import { create } from "zustand";

export interface MediaFile {
  media_id: string;
  file_name: string;
  file_type: string;
  file_size: number;
  storage_url: string;
  status: "processing" | "ready" | "failed";
  created_at: string;
  task_id?: string;
}

interface MediaState {
  files: MediaFile[];
  isLoading: boolean;
  setFiles: (files: MediaFile[]) => void;
  addFiles: (files: MediaFile[]) => void;
  updateFileStatus: (
    taskId: string,
    status: "processing" | "ready" | "failed",
  ) => void;
  setLoading: (loading: boolean) => void;
}

export const useMediaStore = create<MediaState>((set) => ({
  files: [],
  isLoading: false,
  setFiles: (files) => set({ files }),
  addFiles: (newFiles) =>
    set((state) => ({ files: [...newFiles, ...state.files] })),
  updateFileStatus: (taskId, status) =>
    set((state) => ({
      files: state.files.map((file) =>
        file.task_id === taskId ? { ...file, status } : file,
      ),
    })),
  setLoading: (loading) => set({ isLoading: loading }),
}));
