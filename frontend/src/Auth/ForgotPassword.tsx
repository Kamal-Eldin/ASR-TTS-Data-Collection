import { useState } from "react";
import { Link } from "react-router-dom";
import "./Auth.css";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

export default function ForgotPassword() {
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

      if (!res.ok) throw new Error("Request failed");
      setSubmitted(true);
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="sign-in-container">
      <div className="background-image">
        <img src="/background.png" alt="Background" />
      </div>

      <div className="right-side">
        <div className="form-container">
          <div className="card">
            {submitted ? (
              <>
                <div className="card-header">
                  <h2 className="card-title">Check Your Email</h2>
                  <p className="card-description">
                    If an account exists for <strong>{email}</strong>, we've sent
                    a password reset link. Check your inbox and spam folder.
                  </p>
                </div>

                <Link
                  to="/signin"
                  className="sign-in-button"
                  style={{ display: "block", textAlign: "center", textDecoration: "none", marginTop: 16 }}
                >
                  Back to Sign In
                </Link>
              </>
            ) : (
              <>
                <div className="card-header">
                  <h2 className="card-title">Forgot Password</h2>
                  <p className="card-description">
                    Enter your email and we'll send you a reset link
                  </p>
                </div>

                <form className="sign-in-form" onSubmit={handleSubmit}>
                  <div className="form-field">
                    <label className="form-label">Email</label>
                    <div className="input-container">
                      <div className="input-wrapper">
                        <img src="/email-icon.svg" alt="" className="input-icon" />
                        <input
                          type="email"
                          className="form-input with-icon"
                          placeholder="Enter Your Email"
                          value={email}
                          onChange={(e) => {
                            setEmail(e.target.value);
                            if (error) setError("");
                          }}
                        />
                      </div>
                    </div>
                    {error && <p className="form-error">{error}</p>}
                  </div>

                  <button
                    type="submit"
                    className="sign-in-button"
                    disabled={loading}
                    style={{ opacity: loading ? 0.7 : 1 }}
                  >
                    {loading ? "Sending..." : "Send Reset Link"}
                  </button>

                  <Link
                    to="/signin"
                    style={{
                      textAlign: "center",
                      fontSize: "14px",
                      color: "#4F39F6",
                      textDecoration: "none",
                      marginTop: 4,
                    }}
                  >
                    Back to Sign In
                  </Link>
                </form>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
