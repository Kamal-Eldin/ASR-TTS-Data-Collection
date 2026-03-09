import { useEffect, useState } from "react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import "./Auth.css";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get("token") || "";

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [validating, setValidating] = useState(true);
  const [tokenValid, setTokenValid] = useState(false);
  const [success, setSuccess] = useState(false);

  // Validate token on mount
  useEffect(() => {
    if (!token) {
      setValidating(false);
      return;
    }

    fetch(`${BACKEND_URL}/api/password-reset/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    })
      .then((res) => {
        if (!res.ok) throw new Error();
        return res.json();
      })
      .then(() => setTokenValid(true))
      .catch(() => setTokenValid(false))
      .finally(() => setValidating(false));
  }, [token]);

  const getStrength = (pw: string) => {
    if (!pw) return { level: 0, label: "", color: "" };
    let score = 0;
    if (pw.length >= 8) score++;
    if (/[A-Z]/.test(pw)) score++;
    if (/[0-9]/.test(pw)) score++;
    if (/[^A-Za-z0-9]/.test(pw)) score++;
    if (score <= 1) return { level: 1, label: "Weak", color: "red" };
    if (score === 2) return { level: 2, label: "Medium", color: "yellow" };
    return { level: 3, label: "Strong", color: "green" };
  };

  const strength = getStrength(password);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!password) {
      setError("Password is required");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/password-reset/reset`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: password }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => null);
        throw new Error(data?.detail || "Failed to reset password");
      }

      setSuccess(true);
      setTimeout(() => navigate("/signin", { replace: true }), 3000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  // Loading state
  if (validating) {
    return (
      <div className="sign-in-container">
        <div className="background-image">
          <img src="/background.png" alt="Background" />
        </div>
        <div className="right-side">
          <div className="form-container">
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Validating...</h2>
                <p className="card-description">Please wait while we verify your reset link.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Invalid/expired token
  if (!token || !tokenValid) {
    return (
      <div className="sign-in-container">
        <div className="background-image">
          <img src="/background.png" alt="Background" />
        </div>
        <div className="right-side">
          <div className="form-container">
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Invalid Link</h2>
                <p className="card-description">
                  This password reset link is invalid or has expired. Please request a new one.
                </p>
              </div>
              <Link
                to="/forgot-password"
                className="sign-in-button"
                style={{ display: "block", textAlign: "center", textDecoration: "none", marginTop: 16 }}
              >
                Request New Link
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Success state
  if (success) {
    return (
      <div className="sign-in-container">
        <div className="background-image">
          <img src="/background.png" alt="Background" />
        </div>
        <div className="right-side">
          <div className="form-container">
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Password Reset!</h2>
                <p className="card-description">
                  Your password has been updated. Redirecting to sign in...
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Reset form
  return (
    <div className="sign-in-container">
      <div className="background-image">
        <img src="/background.png" alt="Background" />
      </div>

      <div className="right-side">
        <div className="form-container">
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Set New Password</h2>
              <p className="card-description">Enter your new password below</p>
            </div>

            <form className="sign-in-form" onSubmit={handleSubmit}>
              {/* Password */}
              <div className="form-field">
                <label className="form-label password-label">
                  New Password
                  <span className="tooltip">
                    <button type="button" className="tooltip-icon" aria-label="Password requirements">!</button>
                    <span className="tooltip-content">
                      At least 8 characters, include an uppercase letter, a number, and a symbol.
                    </span>
                  </span>
                </label>
                <div className="input-container">
                  <div className="input-wrapper">
                    <img src="/password-icon.svg" alt="" className="input-icon" />
                    <input
                      type={showPassword ? "text" : "password"}
                      className="form-input with-icon with-right-icon"
                      placeholder="Enter new password"
                      value={password}
                      onChange={(e) => {
                        setPassword(e.target.value);
                        if (error) setError("");
                      }}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword((v) => !v)}
                      className="password-toggle"
                    >
                      <img src="/eye-icon.svg" alt="" />
                    </button>
                  </div>
                </div>
              </div>

              {password && (
                <div className={`password-strength ${strength.color}`}>
                  <div className="strength-bars">
                    {[1, 2, 3].map((i) => (
                      <span key={i} className={`strength-bar ${strength.level >= i ? "active" : ""}`} />
                    ))}
                  </div>
                  <span className="strength-label">{strength.label}</span>
                </div>
              )}

              {/* Confirm Password */}
              <div className="form-field">
                <label className="form-label">Confirm Password</label>
                <div className="input-container">
                  <div className="input-wrapper">
                    <img src="/password-icon.svg" alt="" className="input-icon" />
                    <input
                      type={showConfirmPassword ? "text" : "password"}
                      className="form-input with-icon with-right-icon"
                      placeholder="Confirm new password"
                      value={confirmPassword}
                      onChange={(e) => {
                        setConfirmPassword(e.target.value);
                        if (error) setError("");
                      }}
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword((v) => !v)}
                      className="password-toggle"
                    >
                      <img src="/eye-icon.svg" alt="" />
                    </button>
                  </div>
                </div>
              </div>

              {confirmPassword && (
                <div className={`password-strength ${confirmPassword === password ? "green" : "red"}`}>
                  <span className="strength-label">
                    {confirmPassword === password ? "Passwords match" : "Passwords do not match"}
                  </span>
                </div>
              )}

              {error && <p className="form-error">{error}</p>}

              <button
                type="submit"
                className="sign-in-button"
                disabled={loading}
                style={{ opacity: loading ? 0.7 : 1 }}
              >
                {loading ? "Resetting..." : "Reset Password"}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
