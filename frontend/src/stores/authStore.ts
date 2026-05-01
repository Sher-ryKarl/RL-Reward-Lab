import { create } from "zustand";

const TOKEN_KEY = "rl_lab_token";

interface AuthState {
  token: string | null;
  isAuthenticated: boolean;
  login: (token: string) => void;
  logout: () => void;
  getToken: () => string | null;
}

export const useAuthStore = create<AuthState>((set, get) => {
  const stored = localStorage.getItem(TOKEN_KEY);
  return {
    token: stored,
    isAuthenticated: !!stored,
    login: (token: string) => {
      localStorage.setItem(TOKEN_KEY, token);
      set({ token, isAuthenticated: true });
    },
    logout: () => {
      localStorage.removeItem(TOKEN_KEY);
      set({ token: null, isAuthenticated: false });
    },
    getToken: () => get().token,
  };
});
