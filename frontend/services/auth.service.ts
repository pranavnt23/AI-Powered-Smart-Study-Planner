import api, { getCurrentApiBaseUrl } from "@/lib/axios";

import {
  RegisterPayload,
  LoginPayload,
  SendOtpPayload,
  VerifyOtpPayload,
  LogoutPayload,
} from "@/types/auth";

const getApiErrorMessage = (
  error: unknown,
  fallback = "Unable to process request. Please try again."
) => {
  const err = error as any;
  const response = err?.response?.data;

  if (response) {
    if (typeof response.message === "string") {
      return response.message;
    }

    if (typeof response.detail === "string") {
      return response.detail;
    }

    if (typeof response.detail?.message === "string") {
      return response.detail.message;
    }
  }

  if (typeof err?.message === "string") {
    const message = err.message as string;
    if (!message.startsWith("Request failed with status code")) {
      return message;
    }
  }

  return fallback;
};

export const sendOtp = async (
  data: SendOtpPayload
) => {
  try {
    const response = await api.post("/auth/send-otp", data);
    return response.data;
  } catch (error) {
    throw new Error(getApiErrorMessage(error, "Unable to send the verification email. Check the address and try again."));
  }
};

export const verifyOtp = async (
  data: VerifyOtpPayload
) => {
  try {
    const response = await api.post("/auth/verify-otp", data);
    return response.data;
  } catch (error) {
    throw new Error(getApiErrorMessage(error, "Unable to verify the code. Confirm the OTP and try again."));
  }
};

export const registerUser = async (
  data: RegisterPayload
) => {
  try {
    const response = await api.post("/auth/register", data);
    return response.data;
  } catch (error) {
    throw new Error(getApiErrorMessage(error, "Unable to create your account right now. Please review the form and try again."));
  }
};

export const loginUser = async (
  data: LoginPayload
) => {
  try {
    console.log(`Login request API: ${getCurrentApiBaseUrl()}/auth/login`);
    const response = await api.post("/auth/login", data);
    return response.data?.data ?? response.data;
  } catch (error) {
    throw new Error(getApiErrorMessage(error, "Unable to sign in. Verify your credentials and try again."));
  }
};

export const checkBackendConnection = async () => {
  const apiUrl = getCurrentApiBaseUrl();
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), 5000);

  try {
    const response = await fetch(apiUrl, {
      method: "GET",
      cache: "no-store",
      signal: controller.signal,
    });
    const data = await response.json().catch(() => null);

    if (!response.ok) {
      throw new Error(data?.message || `Backend returned ${response.status}`);
    }

    return {
      ok: true,
      message: `${data?.message || "Backend reachable."} API: ${apiUrl}`,
      data,
    };
  } catch (error) {
    const message =
      error instanceof DOMException && error.name === "AbortError"
        ? `Backend check timed out at ${apiUrl}`
        : getApiErrorMessage(error, `Unable to reach backend at ${apiUrl}`);

    throw new Error(message);
  } finally {
    window.clearTimeout(timeoutId);
  }
};

export const logoutUser = async (
  data: LogoutPayload
) => {
  try {
    const response = await api.post("/auth/logout", data);
    return response.data;
  } catch (error) {
    throw new Error(getApiErrorMessage(error, "Unable to log out. Please try again."));
  }
};
