import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { apiFetch, setStoredUser } from "../utils/auth";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

type LanguagePair = {
  language: string;
  level: string;
};

type ProfileForm = {
  id: number;
  email: string;
  firstName: string;
  lastName: string;
  yearOfBirth: string;
  gender: string;
  country: string;
  city: string;
  education: string;
  profession: string;
  languageRelated: string;
  nativeLanguage: string;
  languagePairs: LanguagePair[];
  system: string;
  micType: string;
};

const emptyProfile: ProfileForm = {
  id: 0,
  email: "",
  firstName: "",
  lastName: "",
  yearOfBirth: "",
  gender: "",
  country: "",
  city: "",
  education: "",
  profession: "",
  languageRelated: "",
  nativeLanguage: "",
  languagePairs: [{ language: "", level: "" }],
  system: "",
  micType: "",
};

function Profile() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<ProfileForm>(emptyProfile);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const res = await apiFetch(`${BACKEND_URL}/api/profile`);
        if (!res.ok) {
          throw new Error("Failed to load profile");
        }
        const data = await res.json();
        setProfile({
          ...data,
          languagePairs: data.languagePairs?.length ? data.languagePairs : [{ language: "", level: "" }],
        });
      } catch (error) {
        setMessage("Failed to load profile.");
      } finally {
        setLoading(false);
      }
    };

    loadProfile();
  }, []);

  const handleChange = (field: keyof ProfileForm, value: string) => {
    setProfile((current) => ({ ...current, [field]: value }));
  };

  const updateLanguagePair = (index: number, field: keyof LanguagePair, value: string) => {
    setProfile((current) => {
      const nextPairs = [...current.languagePairs];
      nextPairs[index] = { ...nextPairs[index], [field]: value };
      return { ...current, languagePairs: nextPairs };
    });
  };

  const addLanguagePair = () => {
    setProfile((current) => ({
      ...current,
      languagePairs: [...current.languagePairs, { language: "", level: "" }],
    }));
  };

  const removeLanguagePair = (index: number) => {
    setProfile((current) => {
      const nextPairs = current.languagePairs.filter((_, currentIndex) => currentIndex !== index);
      return {
        ...current,
        languagePairs: nextPairs.length ? nextPairs : [{ language: "", level: "" }],
      };
    });
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage("");

    try {
      const res = await apiFetch(`${BACKEND_URL}/api/profile`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          firstName: profile.firstName,
          lastName: profile.lastName,
          yearOfBirth: profile.yearOfBirth,
          gender: profile.gender,
          country: profile.country,
          city: profile.city,
          education: profile.education,
          profession: profile.profession,
          languageRelated: profile.languageRelated,
          nativeLanguage: profile.nativeLanguage,
          languagePairs: profile.languagePairs,
          system: profile.system,
          micType: profile.micType,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to save profile");
      }

      setProfile({
        ...data,
        languagePairs: data.languagePairs?.length ? data.languagePairs : [{ language: "", level: "" }],
      });
      setStoredUser({
        id: data.id,
        email: data.email,
        firstName: data.firstName,
        lastName: data.lastName,
      });
      setMessage("Profile saved successfully.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to save profile.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center text-gray-500">
          Loading profile...
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Profile</h1>
            <p className="text-gray-500 mt-1">Review and update your account information.</p>
          </div>
          <button
            onClick={() => navigate("/projects")}
            className="bg-gray-100 text-gray-600 rounded-lg px-4 py-2 font-semibold hover:bg-gray-200 transition"
          >
            Back to Projects
          </button>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <label className="block">
            <span className="text-gray-700 font-medium">First Name</span>
            <input
              value={profile.firstName}
              onChange={(event) => handleChange("firstName", event.target.value)}
              className="w-full border border-gray-300 rounded-lg px-4 py-3 mt-1 bg-gray-50"
            />
          </label>
          <label className="block">
            <span className="text-gray-700 font-medium">Last Name</span>
            <input
              value={profile.lastName}
              onChange={(event) => handleChange("lastName", event.target.value)}
              className="w-full border border-gray-300 rounded-lg px-4 py-3 mt-1 bg-gray-50"
            />
          </label>
          <label className="block">
            <span className="text-gray-700 font-medium">Email</span>
            <input
              value={profile.email}
              readOnly
              className="w-full border border-gray-300 rounded-lg px-4 py-3 mt-1 bg-gray-100 text-gray-500"
            />
          </label>
          <label className="block">
            <span className="text-gray-700 font-medium">Year of Birth</span>
            <input
              value={profile.yearOfBirth}
              onChange={(event) => handleChange("yearOfBirth", event.target.value)}
              className="w-full border border-gray-300 rounded-lg px-4 py-3 mt-1 bg-gray-50"
            />
          </label>
          <label className="block">
            <span className="text-gray-700 font-medium">Gender</span>
            <input
              value={profile.gender}
              onChange={(event) => handleChange("gender", event.target.value)}
              className="w-full border border-gray-300 rounded-lg px-4 py-3 mt-1 bg-gray-50"
            />
          </label>
          <label className="block">
            <span className="text-gray-700 font-medium">Country</span>
            <input
              value={profile.country}
              onChange={(event) => handleChange("country", event.target.value)}
              className="w-full border border-gray-300 rounded-lg px-4 py-3 mt-1 bg-gray-50"
            />
          </label>
          <label className="block">
            <span className="text-gray-700 font-medium">City</span>
            <input
              value={profile.city}
              onChange={(event) => handleChange("city", event.target.value)}
              className="w-full border border-gray-300 rounded-lg px-4 py-3 mt-1 bg-gray-50"
            />
          </label>
          <label className="block">
            <span className="text-gray-700 font-medium">Education</span>
            <input
              value={profile.education}
              onChange={(event) => handleChange("education", event.target.value)}
              className="w-full border border-gray-300 rounded-lg px-4 py-3 mt-1 bg-gray-50"
            />
          </label>
          <label className="block">
            <span className="text-gray-700 font-medium">Profession</span>
            <input
              value={profile.profession}
              onChange={(event) => handleChange("profession", event.target.value)}
              className="w-full border border-gray-300 rounded-lg px-4 py-3 mt-1 bg-gray-50"
            />
          </label>
          <label className="block">
            <span className="text-gray-700 font-medium">Language Related</span>
            <input
              value={profile.languageRelated}
              onChange={(event) => handleChange("languageRelated", event.target.value)}
              className="w-full border border-gray-300 rounded-lg px-4 py-3 mt-1 bg-gray-50"
            />
          </label>
          <label className="block">
            <span className="text-gray-700 font-medium">Native Language</span>
            <input
              value={profile.nativeLanguage}
              onChange={(event) => handleChange("nativeLanguage", event.target.value)}
              className="w-full border border-gray-300 rounded-lg px-4 py-3 mt-1 bg-gray-50"
            />
          </label>
          <label className="block">
            <span className="text-gray-700 font-medium">Operating System</span>
            <input
              value={profile.system}
              onChange={(event) => handleChange("system", event.target.value)}
              className="w-full border border-gray-300 rounded-lg px-4 py-3 mt-1 bg-gray-50"
            />
          </label>
          <label className="block md:col-span-2">
            <span className="text-gray-700 font-medium">Microphone Type</span>
            <input
              value={profile.micType}
              onChange={(event) => handleChange("micType", event.target.value)}
              className="w-full border border-gray-300 rounded-lg px-4 py-3 mt-1 bg-gray-50"
            />
          </label>
        </div>

        <div className="mt-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">Language Pairs</h2>
            <button
              type="button"
              onClick={addLanguagePair}
              className="bg-gray-100 text-gray-700 rounded-lg px-4 py-2 font-semibold hover:bg-gray-200 transition"
            >
              Add Pair
            </button>
          </div>
          <div className="space-y-3">
            {profile.languagePairs.map((pair, index) => (
              <div key={index} className="grid gap-3 md:grid-cols-3">
                <input
                  value={pair.language}
                  onChange={(event) => updateLanguagePair(index, "language", event.target.value)}
                  placeholder="Language"
                  className="w-full border border-gray-300 rounded-lg px-4 py-3 bg-gray-50"
                />
                <input
                  value={pair.level}
                  onChange={(event) => updateLanguagePair(index, "level", event.target.value)}
                  placeholder="Level"
                  className="w-full border border-gray-300 rounded-lg px-4 py-3 bg-gray-50"
                />
                <button
                  type="button"
                  onClick={() => removeLanguagePair(index)}
                  className="bg-red-50 text-red-600 rounded-lg px-4 py-3 font-semibold hover:bg-red-100 transition"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-8 flex items-center justify-between border-t border-gray-200 pt-6">
          <div className={`text-sm font-medium ${message.includes("success") ? "text-green-600" : "text-red-600"}`}>
            {message}
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => navigate("/projects")}
              className="bg-gray-100 text-gray-600 rounded-lg px-5 py-2 font-semibold hover:bg-gray-200 transition"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="bg-gray-900 text-white rounded-lg px-5 py-2 font-semibold hover:bg-gray-800 transition disabled:opacity-50"
            >
              {saving ? "Saving..." : "Save"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Profile;
