"use client";

import { useState } from "react";

import "./LoginForm.css";

import { loginUser } from "@/services/auth.service";

export default function LoginForm() {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (
    e: React.FormEvent
  ) => {
    e.preventDefault();

    try {
      const response = await loginUser(formData);

      localStorage.setItem(
        "token",
        response.data.access_token
      );

      alert(response.message);

    } catch (error: any) {
      alert(
        error.response?.data?.message ||
        "Login failed"
      );
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="login-form"
    >
      <div className="login-input-group">
        <label>Email Address</label>

        <input
          type="email"
          name="email"
          placeholder="Enter your email"
          onChange={handleChange}
          required
        />
      </div>

      <div className="login-input-group">
        <label>Password</label>

        <input
          type="password"
          name="password"
          placeholder="Enter your password"
          onChange={handleChange}
          required
        />
      </div>

      <button type="submit">
        Login
      </button>
    </form>
  );
}