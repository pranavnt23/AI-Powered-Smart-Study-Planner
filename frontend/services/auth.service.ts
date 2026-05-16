import api from "@/lib/axios";

import {
  RegisterPayload,
  LoginPayload,
} from "@/types/auth";

export const registerUser = async (
  data: RegisterPayload
) => {

  const response = await api.post(
    "/auth/register",
    data
  );

  return response.data;
};

export const loginUser = async (
  data: LoginPayload
) => {

  const response = await api.post(
    "/auth/login",
    data
  );

  return response.data;
};