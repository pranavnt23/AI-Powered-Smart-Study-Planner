"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import "./RegisterForm.css";

import {
  registerUser,
  sendOtp,
  verifyOtp,
} from "@/services/auth.service";

export default function RegisterForm() {
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [otpValue, setOtpValue] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [emailVerified, setEmailVerified] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<{
    username?: string;
    email?: string;
    password?: string;
    confirmPassword?: string;
    otp?: string;
  }>({});
  const [statusMessage, setStatusMessage] = useState("");
  const [statusType, setStatusType] = useState<"error" | "success" | "">("");
  const [sendingOtp, setSendingOtp] = useState(false);
  const [verifyingOtp, setVerifyingOtp] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const router = useRouter();

  const validateEmail = (email: string) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  };

  const clearFieldError = (field: keyof typeof fieldErrors) => {
    setFieldErrors((prev) => ({
      ...prev,
      [field]: undefined,
    }));
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const { name, value } = e.target;

    if (name === "email") {
      setEmailVerified(false);
      setOtpSent(false);
      setOtpValue("");
      setStatusMessage("");
      setStatusType("");
    }

    setFormData({
      ...formData,
      [name]: value,
    });

    clearFieldError(name as keyof typeof fieldErrors);
  };

  const handleSendOtp = async () => {
    const email = formData.email.trim();

    if (!email) {
      setFieldErrors({ email: "Email address is required." });
      setStatusMessage("Enter the email address you want to verify.");
      setStatusType("error");
      return;
    }

    if (!validateEmail(email)) {
      setFieldErrors({ email: "Enter a valid email address, for example name@example.com." });
      setStatusMessage("Use a valid email address to receive the verification code.");
      setStatusType("error");
      return;
    }

    setSendingOtp(true);
    setStatusMessage("");
    setStatusType("");
    setFieldErrors({});

    try {
      await sendOtp({ email: formData.email });
      setOtpSent(true);
      setStatusMessage("OTP sent. Please check your inbox.");
      setStatusType("success");
    } catch (error: any) {
      const message =
        error instanceof Error
          ? error.message
          : "Unable to send OTP. Please try again.";

      setStatusMessage(message);
      setStatusType("error");
    } finally {
      setSendingOtp(false);
    }
  };

  const handleVerifyOtp = async () => {
    if (!otpValue.trim()) {
      setFieldErrors({ otp: "One-time password is required." });
      setStatusMessage("Enter the OTP code that was emailed to you.");
      setStatusType("error");
      return;
    }

    setVerifyingOtp(true);
    setStatusMessage("");
    setStatusType("");
    setFieldErrors({});

    try {
      await verifyOtp({
        email: formData.email,
        otp: otpValue,
      });

      setEmailVerified(true);
      setStatusMessage("Email verified successfully. You can now register.");
      setStatusType("success");
    } catch (error: any) {
      const message =
        error instanceof Error
          ? error.message
          : "OTP verification failed.";

      setStatusMessage(message);
      setStatusType("error");
    } finally {
      setVerifyingOtp(false);
    }
  };

  const handleSubmit = async (
    e: React.FormEvent
  ) => {
    e.preventDefault();

    const errors: typeof fieldErrors = {};

    if (!formData.username.trim()) {
      errors.username = "Username is required.";
    }

    if (!formData.email.trim()) {
      errors.email = "Email address is required.";
    } else if (!validateEmail(formData.email.trim())) {
      errors.email = "Enter a valid email address, for example name@example.com.";
    }

    if (!formData.password.trim()) {
      errors.password = "Password is required.";
    } else if (formData.password.length < 8) {
      errors.password = "Password must be at least 8 characters long.";
    }

    if (!formData.confirmPassword.trim()) {
      errors.confirmPassword = "Confirm your password.";
    } else if (formData.confirmPassword !== formData.password) {
      errors.confirmPassword = "Passwords do not match.";
    }

    if (!emailVerified) {
      errors.email = errors.email || "Email verification is required before creating your account.";
    }

    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      setStatusMessage(
        "Review the highlighted fields and fix any errors before submitting."
      );
      setStatusType("error");
      return;
    }

    setSubmitting(true);
    setStatusMessage("");
    setStatusType("");

    try {
      const response = await registerUser({
        username: formData.username,
        email: formData.email,
        password: formData.password,
      });
      setStatusMessage(response.message);
      setStatusType("success");
      router.push("/dashboard");
    } catch (error: any) {
      const message =
        error instanceof Error
          ? error.message
          : "Registration failed.";

      setStatusMessage(message);
      setStatusType("error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="register-form" noValidate>
      <div className="register-input-group">
        <label>Username</label>

        <input
          type="text"
          name="username"
          placeholder="Enter your username"
          onChange={handleChange}
          value={formData.username}
          className={fieldErrors.username ? "input-error" : ""}
        />

        {fieldErrors.username && (
          <p className="field-error">{fieldErrors.username}</p>
        )}
      </div>

      <div className="register-input-group">
        <label>Email Address</label>

        <div className="email-verification-row">
          <input
            type="email"
            name="email"
            placeholder="Enter your email"
            onChange={handleChange}
            value={formData.email}
            className={fieldErrors.email ? "input-error" : ""}
          />

          <button
            type="button"
            className="verification-button"
            onClick={handleSendOtp}
            disabled={sendingOtp || !formData.email || emailVerified}
          >
            {emailVerified ? "Verified" : sendingOtp ? "Sending…" : "Verify Mail"}
          </button>
        </div>
        {fieldErrors.email && (
          <p className="field-error">{fieldErrors.email}</p>
        )}
      </div>

      {otpSent && !emailVerified && (
        <div className="register-input-group">
          <label>OTP Code</label>

          <div className="otp-row">
            <input
              type="text"
              name="otp"
              placeholder="Enter OTP"
              value={otpValue}
              onChange={(e) => {
                setOtpValue(e.target.value);
                if (fieldErrors.otp) {
                  setFieldErrors((prev) => ({ ...prev, otp: undefined }));
                }
              }}
              className={fieldErrors.otp ? "input-error" : ""}
            />

            <button
              type="button"
              className="verification-button"
              onClick={handleVerifyOtp}
              disabled={verifyingOtp}
            >
              {verifyingOtp ? "Verifying…" : "Verify"}
            </button>
          </div>
          {fieldErrors.otp && (
            <p className="field-error">{fieldErrors.otp}</p>
          )}
        </div>
      )}

      <div className="register-input-group">
        <label>Password</label>

        <input
          type="password"
          name="password"
          placeholder="Create your password"
          onChange={handleChange}
          value={formData.password}
          className={fieldErrors.password ? "input-error" : ""}
        />
        <p className="field-help">
          Use at least 8 characters for a secure password.
        </p>
        {fieldErrors.password && (
          <p className="field-error">{fieldErrors.password}</p>
        )}
      </div>

      <div className="register-input-group">
        <label>Confirm Password</label>

        <input
          type="password"
          name="confirmPassword"
          placeholder="Re-enter your password"
          onChange={handleChange}
          value={formData.confirmPassword}
          className={fieldErrors.confirmPassword ? "input-error" : ""}
        />
        {fieldErrors.confirmPassword && (
          <p className="field-error">{fieldErrors.confirmPassword}</p>
        )}
      </div>

      {statusMessage && (
        <p className={`status-message ${statusType}`}>
          {statusMessage}
        </p>
      )}

      <button type="submit" disabled={submitting}>
        {submitting ? "Creating account…" : "Create Account"}
      </button>
    </form>
  );
}
