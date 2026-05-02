import { create } from "zustand";

const TOKEN_KEY = "rl_lab_token";
const USER_KEY = "rl_lab_user";

interface UserInfo {
  id: string;
  username: string;
}

interface AuthState {
  token: string | null;
  user: UserInfo | null;
  isAuthenticated: boolean;
  login: (token: string, user: UserInfo) => void;
  logout: () => void;
  getToken: () => string | null;
}

function loadUser(): UserInfo | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export const useAuthStore = create<AuthState>((set, get) => {
  const stored = localStorage.getItem(TOKEN_KEY);
  return {
    token: stored,
    user: stored ? loadUser() : null,
    isAuthenticated: !!stored,
    login: (token: string, user: UserInfo) => {
      localStorage.setItem(TOKEN_KEY, token);
      localStorage.setItem(USER_KEY, JSON.stringify(user));
      set({ token, user, isAuthenticated: true });
    },
    logout: () => {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
      set({ token: null, user: null, isAuthenticated: false });
    },
    getToken: () => get().token,
  };
});
