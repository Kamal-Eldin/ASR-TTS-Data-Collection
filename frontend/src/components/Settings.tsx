import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { apiFetch } from '../utils/auth';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

function Settings() {
  const navigate = useNavigate();
  const [settings, setSettings] = useState({
    storage_path: '',
    s3_bucket: '',
    huggingface_token: '',
    huggingface_repo: '',
  });
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');
  const [showClearModal, setShowClearModal] = useState(false);
  const [isClearing, setIsClearing] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const res = await apiFetch(`${BACKEND_URL}/settings/`);
      const data = await res.json();
      setSettings(data);
    } catch (error) {
      console.error('Failed to fetch settings:', error);
    }
  };

  const handleSettingsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSettings({ ...settings, [e.target.name]: e.target.value });
  };

  const saveSettings = async () => {
    setIsSaving(true);
    setSaveMessage('');

    try {
      const res = await apiFetch(`${BACKEND_URL}/settings/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });

      if (res.ok) {
        setSaveMessage('Settings saved successfully.');
        setTimeout(() => setSaveMessage(''), 3000);
      } else {
        setSaveMessage('Failed to save settings. Please try again.');
      }
    } catch (error) {
      setSaveMessage('Error saving settings. Please check your connection.');
    } finally {
      setIsSaving(false);
    }
  };

  const clearDatabase = async () => {
    setIsClearing(true);

    try {
      const res = await apiFetch(`${BACKEND_URL}/clear_database/`, {
        method: 'POST',
      });
      const data = await res.json();

      if (data.status === 'ok') {
        setShowClearModal(false);
        alert('Your data was cleared successfully. The page will refresh.');
        window.location.reload();
      } else {
        alert(`Error: ${data.detail}`);
      }
    } catch (error) {
      alert('Failed to clear your data. Please try again.');
    } finally {
      setIsClearing(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
            <p className="text-gray-500 mt-1">Configure your application preferences.</p>
          </div>
          <button
            onClick={() => navigate("/projects")}
            className="bg-gray-100 text-gray-600 rounded-lg px-4 py-2 font-semibold hover:bg-gray-200 transition"
          >
            Back to Projects
          </button>
        </div>

        <div className="space-y-6">
          <div className="bg-gray-50 rounded-lg p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Storage Settings</h2>
            <label className="block">
              <span className="text-gray-700 font-medium">Local Storage Path</span>
              <input
                name="storage_path"
                value={settings.storage_path}
                onChange={handleSettingsChange}
                className="w-full border border-gray-300 rounded-lg px-4 py-3 text-base bg-white text-gray-900 outline-none mt-1 focus:border-gray-500"
                placeholder="e.g., recordings, /path/to/recordings"
              />
              <p className="text-sm text-gray-500 mt-1">Directory where your audio files will be stored locally.</p>
            </label>
          </div>

          <div className="bg-gray-50 rounded-lg p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Amazon S3 Settings</h2>
            <label className="block">
              <span className="text-gray-700 font-medium">S3 Bucket Name</span>
              <input
                name="s3_bucket"
                value={settings.s3_bucket}
                onChange={handleSettingsChange}
                className="w-full border border-gray-300 rounded-lg px-4 py-3 text-base bg-white text-gray-900 outline-none mt-1 focus:border-gray-500"
                placeholder="e.g., my-voice-datasets"
              />
              <p className="text-sm text-gray-500 mt-1">Bucket where your datasets will be exported.</p>
            </label>
          </div>

          <div className="bg-gray-50 rounded-lg p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Hugging Face Settings</h2>
            <label className="block mb-4">
              <span className="text-gray-700 font-medium">Hugging Face Token</span>
              <input
                name="huggingface_token"
                value={settings.huggingface_token}
                onChange={handleSettingsChange}
                type="password"
                className="w-full border border-gray-300 rounded-lg px-4 py-3 text-base bg-white text-gray-900 outline-none mt-1 focus:border-gray-500"
                placeholder="hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
              />
              <p className="text-sm text-gray-500 mt-1">
                Your Hugging Face access token.
              </p>
            </label>
            <label className="block">
              <span className="text-gray-700 font-medium">Hugging Face Repository</span>
              <input
                name="huggingface_repo"
                value={settings.huggingface_repo}
                onChange={handleSettingsChange}
                className="w-full border border-gray-300 rounded-lg px-4 py-3 text-base bg-white text-gray-900 outline-none mt-1 focus:border-gray-500"
                placeholder="e.g., username/dataset-name"
              />
              <p className="text-sm text-gray-500 mt-1">Repository where your datasets will be uploaded.</p>
            </label>
          </div>

          <div className="flex justify-end pt-6 border-t border-gray-200">
            <div className="flex items-center gap-4">
              {saveMessage && (
                <span className={`text-sm font-medium ${saveMessage.includes('successfully') ? 'text-green-600' : 'text-red-600'}`}>
                  {saveMessage}
                </span>
              )}
              <button
                onClick={saveSettings}
                disabled={isSaving}
                className="bg-gray-900 text-white rounded-lg px-8 py-3 font-semibold hover:bg-gray-800 transition disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
              >
                {isSaving ? 'Saving...' : 'Save Settings'}
              </button>
            </div>
          </div>
        </div>

        <div className="mt-12 p-6 bg-red-50 rounded-lg border border-red-200">
          <h2 className="text-xl font-bold text-red-800 mb-4">Data Management</h2>
          <div className="space-y-4">
            <div>
              <h3 className="font-semibold text-red-700 mb-2">Clear My Data</h3>
              <p className="text-sm text-red-600 mb-4">
                This will permanently delete your projects, recordings, settings, and audio files.
                This action cannot be undone.
              </p>
              <button
                onClick={() => setShowClearModal(true)}
                className="bg-red-600 text-white rounded-lg px-6 py-3 font-semibold hover:bg-red-700 transition shadow-sm"
              >
                Clear My Data
              </button>
            </div>
          </div>
        </div>

        <div className="mt-12 p-6 bg-gray-50 rounded-lg border border-gray-200">
          <h2 className="text-lg font-bold text-gray-900 mb-3">Getting Started</h2>
          <div className="space-y-2 text-sm text-gray-700">
            <p>1. Set a storage path for your recordings.</p>
            <p>2. Configure S3 if you want cloud export.</p>
            <p>3. Add your Hugging Face token and repository for dataset sharing.</p>
            <p>4. Return to Projects to continue recording.</p>
          </div>
        </div>

        {showClearModal && (
          <div className="fixed top-0 left-0 w-screen h-screen bg-black/60 z-50 flex items-center justify-center">
            <div className="bg-white p-8 rounded-lg min-w-[500px] shadow-lg">
              <div className="text-center mb-6">
                <h2 className="font-bold text-2xl text-red-600 mb-2">Clear My Data</h2>
                <p className="text-gray-600">This action cannot be undone.</p>
              </div>

              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                <h3 className="font-semibold text-red-800 mb-2">What will be deleted:</h3>
                <ul className="text-sm text-red-700 space-y-1">
                  <li>Your projects and their metadata</li>
                  <li>Your recorded audio files</li>
                  <li>Your application settings</li>
                </ul>
              </div>

              <div className="flex justify-center gap-4">
                <button
                  onClick={() => setShowClearModal(false)}
                  disabled={isClearing}
                  className="bg-gray-100 text-gray-600 rounded-lg px-6 py-3 font-semibold hover:bg-gray-200 transition disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={clearDatabase}
                  disabled={isClearing}
                  className="bg-red-600 text-white rounded-lg px-6 py-3 font-semibold hover:bg-red-700 transition disabled:opacity-50 shadow-sm"
                >
                  {isClearing ? 'Clearing...' : 'Yes, Clear My Data'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Settings;
