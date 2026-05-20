"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import "./LoginForm.css";

import { checkBackendConnection, loginUser } from "@/services/auth.service";
import { getCurrentApiBaseUrl } from "@/lib/axios";

const FRONTEND_BUILD_MARKER = "direct-api-v4";

export default function LoginForm() {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const [formErrors, setFormErrors] = useState<{
    email?: string;
    password?: string;
  }>({});
  const [statusMessage, setStatusMessage] = useState("");
  const [connectionStatus, setConnectionStatus] = useState<{
    type: "checking" | "success" | "error";
    message: string;
  }>({
    type: "checking",
    message: "Checking backend connection...",
  });
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);

  const runConnectionCheck = useCallback(async () => {
    const apiUrl = getCurrentApiBaseUrl();

    setConnectionStatus({
      type: "checking",
      message: `Frontend ${FRONTEND_BUILD_MARKER}. Trying ${apiUrl}`,
    });

    try {
      const result = await checkBackendConnection();
      setConnectionStatus({
        type: "success",
        message: result.message,
      });
    } catch (error) {
      setConnectionStatus({
        type: "error",
        message: error instanceof Error ? error.message : "Backend connection check failed.",
      });
    }
  }, []);

  useEffect(() => {
    void runConnectionCheck();
  }, [runConnectionCheck]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const { name, value } = e.target;

    setFormData({
      ...formData,
      [name]: value,
    });

    setFormErrors((prev) => ({
      ...prev,
      [name]: undefined,
    }));
    setStatusMessage("");
  };

  const handleSubmit = async () => {
    const errors: typeof formErrors = {};

    if (!formData.email.trim()) {
      errors.email = "Email or username is required.";
    } else if (formData.email.trim().includes(" ")) {
      errors.email = "Email or username cannot contain spaces.";
    }

    if (!formData.password.trim()) {
      errors.password = "Password is required.";
    }

    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      setStatusMessage("Review the highlighted fields and correct any errors.");
      return;
    }

    try {
      setSubmitting(true);
      const response = await loginUser(formData);

      localStorage.setItem("token", response.access_token);
      if (response.session_id) {
        localStorage.setItem("sessionId", String(response.session_id));
      }
      if (response.expires_at) {
        localStorage.setItem("tokenExpiresAt", response.expires_at);
      }

      setStatusMessage("Login successful. Redirecting to dashboard...");
      router.push("/dashboard");
    } catch (error: any) {
      const message =
        error instanceof Error
          ? error.message
          : "Unable to sign in at this time.";

      setStatusMessage(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        void handleSubmit();
      }}
      className="login-form"
      method="post"
      action="#"
      noValidate
    >
      <div className="login-input-group">
        <label>Email or Username</label>

        <input
          type="text"
          name="email"
          placeholder="Enter your email or username"
          onChange={handleChange}
          value={formData.email}
          className={formErrors.email ? "input-error" : ""}
        />
        {formErrors.email && (
          <p className="field-error">{formErrors.email}</p>
        )}
      </div>

      <div className="login-input-group">
        <label>Password</label>

        <input
          type="password"
          name="password"
          placeholder="Enter your password"
          onChange={handleChange}
          value={formData.password}
          className={formErrors.password ? "input-error" : ""}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              void handleSubmit();
            }
          }}
        />
        {formErrors.password && (
          <p className="field-error">{formErrors.password}</p>
        )}
      </div>

      {statusMessage && (
        <p className="field-error" style={{ marginBottom: 8 }}>
          {statusMessage}
        </p>
      )}

      <button type="button" disabled={submitting} onClick={() => void handleSubmit()}>
        {submitting ? "Signing in..." : "Login"}
      </button>

      <div className={`connection-status ${connectionStatus.type}`}>
        <div>
          <span>Backend</span>
          <p>{connectionStatus.message}</p>
          <small>Frontend build: {FRONTEND_BUILD_MARKER}</small>
        </div>
        <button type="button" onClick={() => void runConnectionCheck()}>
          Retry
        </button>
      </div>
    </form>
  );
}
