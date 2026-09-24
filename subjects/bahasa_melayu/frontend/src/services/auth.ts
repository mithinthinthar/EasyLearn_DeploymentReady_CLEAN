import type { LoginResponse } from "../types/auth";

import { API_URL } from "./config";
const BASE_URL = API_URL;

async function handleResponse(res: Response): Promise<LoginResponse> {
  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(data.detail || data.error || "Request failed");
  }

  return data;
}

export async function loginWithGoogle(token: string): Promise<LoginResponse> {
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ token }),
  });

  return handleResponse(res);
}

export async function loginFromPortal(): Promise<LoginResponse> {
  const res = await fetch(`${BASE_URL}/auth/portal-login`, {
    method: "POST",
    credentials: "include",
  });
  return handleResponse(res);
}

export async function loginWithEmail(
  email: string,
  password: string
): Promise<LoginResponse> {
  const res = await fetch(`${BASE_URL}/auth/email-login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email: email.trim().toLowerCase(),
      password,
    }),
  });

  return handleResponse(res);
}

export async function registerWithEmail(
  email: string,
  password: string
): Promise<LoginResponse> {
  const res = await fetch(`${BASE_URL}/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email: email.trim().toLowerCase(),
      password,
    }),
  });

  return handleResponse(res);
}
