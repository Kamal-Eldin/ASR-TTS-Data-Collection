import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import "./PasswordReset.css";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get("token") || "";

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [validating, setValidating] = useState(true);
  const [tokenValid, setTokenValid] = useState(false);
  const [success, setSuccess] = useState(false);

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
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => navigate("/signin", { replace: true });

  return (
    <div className="pr-page">
      <div className="pr-card">
        <div className="pr-card-header">Voice Force</div>

        <div className="pr-card-body">
          {validating ? (
            <p className="pr-muted">Validating reset link…</p>
          ) : !token || !tokenValid ? (
            <>
              <p className="pr-message">
                This password reset link is invalid or has expired.
                {"\n"}Please request a new one.
              </p>
              <div className="pr-buttons">
                <button
                  type="button"
                  className="pr-btn"
                  onClick={() => navigate("/forgot-password", { replace: true })}
                >
                  Request New Link
                </button>
                <button type="button" className="pr-btn" onClick={handleCancel}>
                  Cancel
                </button>
              </div>
            </>
          ) : success ? (
            <div>
              <p className="pr-success-title">Password Changed !</p>
              <p className="pr-message">You can close this window.</p>
            </div>
          ) : (
            <form className="pr-form" onSubmit={handleSubmit} noValidate>
              <p className="pr-message">
                Please, enter your new password then click save or cancel to
                return back to the login page.
              </p>

              <div className="pr-grid">
                <label className="pr-label" htmlFor="pr-new-pw">New password</label>
                <div className="pr-input-wrapper">
                  <img src="/password-icon.svg" alt="" className="pr-input-icon" />
                  <input
                    id="pr-new-pw"
                    type="password"
                    className="pr-input"
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      if (error) setError("");
                    }}
                    autoFocus
                  />
                </div>

                <label className="pr-label" htmlFor="pr-confirm-pw">Confirm new password</label>
                <div className="pr-input-wrapper">
                  <img src="/password-icon.svg" alt="" className="pr-input-icon" />
                  <input
                    id="pr-confirm-pw"
                    type="password"
                    className="pr-input"
                    value={confirmPassword}
                    onChange={(e) => {
                      setConfirmPassword(e.target.value);
                      if (error) setError("");
                    }}
                  />
                </div>
              </div>

              {error && <p className="pr-error">{error}</p>}

              <div className="pr-buttons">
                <button type="submit" className="pr-btn" disabled={loading}>
                  {loading ? "Saving..." : "Save"}
                </button>
                <button
                  type="button"
                  className="pr-btn"
                  onClick={handleCancel}
                  disabled={loading}
                >
                  Cancel
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
