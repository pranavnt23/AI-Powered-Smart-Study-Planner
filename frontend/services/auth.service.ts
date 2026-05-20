import api from "@/lib/axios";

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
    const response = await api.post("/auth/login", data);
    return response.data?.data ?? response.data;
  } catch (error) {
    throw new Error(getApiErrorMessage(error, "Unable to sign in. Verify your credentials and try again."));
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
