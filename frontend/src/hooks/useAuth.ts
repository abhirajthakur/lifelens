import { api } from "@/lib/api";
import type { AuthResponse } from "@/lib/api-types";
import { useAuthStore } from "@/stores/authStore";
import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import { toast } from "sonner";

export function useLogin() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);

  return useMutation<AuthResponse, Error, { email: string; password: string }>({
    mutationFn: ({ email, password }) => api.login(email, password),
    onSuccess: (data) => {
      setAuth(data.access_token);
      toast.success("Welcome back!");
      navigate("/dashboard");
    },
    onError: (error) => {
      toast.error(error.message || "Login failed");
    },
  });
}

export function useSignup() {
  const navigate = useNavigate();

  return useMutation<
    AuthResponse,
    Error,
    { email: string; password: string; name: string }
  >({
    mutationFn: ({ email, password, name }) =>
      api.signup(email, password, name),
    onSuccess: () => {
      toast.success("Account created! Please sign in.");
      navigate("/login");
    },
    onError: (error) => {
      toast.error(error.message || "Signup failed");
    },
  });
}
