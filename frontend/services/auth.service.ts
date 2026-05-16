import api from "@/lib/axios";

import {
  RegisterPayload,
  LoginPayload,
  SendOtpPayload,
  VerifyOtpPayload,
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
    throw new Error(getApiErrorMessage(error, "Unable to send OTP. Please try again."));
  }
};

export const verifyOtp = async (
  data: VerifyOtpPayload
) => {
  try {
    const response = await api.post("/auth/verify-otp", data);
    return response.data;
  } catch (error) {
    throw new Error(getApiErrorMessage(error, "OTP verification failed. Please try again."));
  }
};

export const registerUser = async (
  data: RegisterPayload
) => {
  try {
    const response = await api.post("/auth/register", data);
    return response.data;
  } catch (error) {
    throw new Error(getApiErrorMessage(error, "Registration failed. Please try again."));
  }
};

export const loginUser = async (
  data: LoginPayload
) => {
  try {
    const response = await api.post("/auth/login", data);
    return response.data;
  } catch (error) {
    throw new Error(getApiErrorMessage(error, "Login failed. Please try again."));
  }
};
