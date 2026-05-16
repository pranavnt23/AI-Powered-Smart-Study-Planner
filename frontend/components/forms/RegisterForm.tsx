"use client";

import { useState } from "react";

import "./RegisterForm.css";

import { registerUser } from "@/services/auth.service";

export default function RegisterForm() {
  const [formData, setFormData] = useState({
    username: "",
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
      const response = await registerUser(formData);

      alert(response.message);

    } catch (error: any) {
      alert(
        error.response?.data?.message ||
        "Registration failed"
      );
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="register-form"
    >
      <div className="register-input-group">
        <label>Username</label>

        <input
          type="text"
          name="username"
          placeholder="Enter your username"
          onChange={handleChange}
          required
        />
      </div>

      <div className="register-input-group">
        <label>Email Address</label>

        <input
          type="email"
          name="email"
          placeholder="Enter your email"
          onChange={handleChange}
          required
        />
      </div>

      <div className="register-input-group">
        <label>Password</label>

        <input
          type="password"
          name="password"
          placeholder="Create your password"
          onChange={handleChange}
          required
        />
      </div>

      <button type="submit">
        Create Account
      </button>
    </form>
  );
}