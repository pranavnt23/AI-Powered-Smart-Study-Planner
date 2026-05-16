"use client";

import { useState } from "react";

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
  });
  const [otpValue, setOtpValue] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [emailVerified, setEmailVerified] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [statusType, setStatusType] = useState<"error" | "success" | "">("");
  const [sendingOtp, setSendingOtp] = useState(false);
  const [verifyingOtp, setVerifyingOtp] = useState(false);

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
  };

  const handleSendOtp = async () => {
    if (!formData.email) {
      setStatusMessage("Enter a valid email address before sending OTP.");
      setStatusType("error");
      return;
    }

    setSendingOtp(true);
    setStatusMessage("");
    setStatusType("");

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
    if (!otpValue) {
      setStatusMessage("Enter the OTP sent to your email.");
      setStatusType("error");
      return;
    }

    setVerifyingOtp(true);
    setStatusMessage("");
    setStatusType("");

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

    if (!emailVerified) {
      setStatusMessage(
        "Please verify your email before creating an account."
      );
      setStatusType("error");
      return;
    }

    try {
      const response = await registerUser(formData);
      alert(response.message);
    } catch (error: any) {
      const message =
        error instanceof Error
          ? error.message
          : "Registration failed.";

      setStatusMessage(message);
      setStatusType("error");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="register-form">
      <div className="register-input-group">
        <label>Username</label>

        <input
          type="text"
          name="username"
          placeholder="Enter your username"
          onChange={handleChange}
          value={formData.username}
          required
        />
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
            required
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
              onChange={(e) => setOtpValue(e.target.value)}
              required
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
          required
        />
      </div>

      {statusMessage && (
        <p className={`status-message ${statusType}`}>
          {statusMessage}
        </p>
      )}

      <button type="submit" disabled={!emailVerified}>
        Create Account
      </button>
    </form>
  );
}
