import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./PasswordReset.css";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

export default function ForgotPassword() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!email.trim()) {
      setError("Email is required");
      return;
    }
    if (!/^\S+@\S+\.\S+$/.test(email)) {
      setError("Please enter a valid email");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/password-reset/forgot`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      if (!res.ok) throw new Error();
      setSubmitted(true);
    } catch {
      setError("Something went wrong. Please try again.");
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
          {submitted ? (
            <p className="pr-message">
              If we find this email in our data, you should receive a reset
              password email shortly.
              {"\n"}Please check your spam folder.
              {"\n"}You can close this window.
            </p>
          ) : (
            <form className="pr-form" onSubmit={handleSubmit} noValidate>
              <p className="pr-message">Enter your login email to reset your password</p>

              <div className="pr-input-wrapper">
                <img src="/email-icon.svg" alt="" className="pr-input-icon" />
                <input
                  type="email"
                  className="pr-input"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (error) setError("");
                  }}
                  autoFocus
                />
              </div>

              {error && <p className="pr-error">{error}</p>}

              <div className="pr-buttons">
                <button type="submit" className="pr-btn" disabled={loading}>
                  {loading ? "Sending..." : "Send"}
                </button>
                <button type="button" className="pr-btn" onClick={handleCancel} disabled={loading}>
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
