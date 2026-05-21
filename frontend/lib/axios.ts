import axios from "axios";

const getApiBaseUrl = () => {
  if (typeof window !== "undefined") {
    const { hostname } = window.location;
    const isLocalFrontend = hostname === "localhost" || hostname === "127.0.0.1";
    const backendHost = isLocalFrontend ? "127.0.0.1" : hostname;

    return `http://${backendHost}:8000`;
  }

  return process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
};

const api = axios.create({
  timeout: 8000,
});

api.interceptors.request.use((config) => {
  config.baseURL = getApiBaseUrl();
  return config;
});

export default api;
