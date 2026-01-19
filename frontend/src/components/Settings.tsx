import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchJson, API_BASE, authHeaders } from '../utils/api';

type SettingsPayload = {
  storage_path: string;
  s3_bucket: string;
  huggingface_token: string;
  huggingface_repo: string;
};

function Settings() {
  const navigate = useNavigate();
  const token = localStorage.getItem('token');
  const [settings, setSettings] = useState<SettingsPayload>({
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
    if (token) fetchSettings();
  }, [token]);

  const fetchSettings = async () => {
    try {
      const data = await fetchJson<SettingsPayload>(`/api/v1/settings/`, token || undefined);
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
      await fetchJson(`/api/v1/settings/`, token || undefined, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify(settings),
      });
      setSaveMessage('Settings saved successfully!');
      setTimeout(() => setSaveMessage(''), 3000);
    } catch (error) {
      setSaveMessage('Failed to save settings. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const clearUserData = async () => {
    setIsClearing(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/exports/clear_user_data/`, {
        method: 'POST',
        headers: authHeaders(token || undefined),
      });
      const data = await res.json();
      if (data.status === 'ok') {
        setShowClearModal(false);
        alert('All your data has been cleared.');
        window.location.reload();
      } else {
        alert(`Error: ${data.detail || 'Failed to clear data'}`);
      }
    } catch (error) {
      alert('Failed to clear data. Please try again.');
    } finally {
      setIsClearing(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <button
          onClick={() => navigate('/')}
          className="p-2 rounded-xl hover:bg-white/80 transition-colors"
        >
          <svg className="w-5 h-5 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-800">Settings</h1>
          <p className="text-slate-500 mt-1">Configure your application preferences</p>
        </div>
      </div>

      {/* Settings Cards */}
      <div className="space-y-6">
        {/* Storage Settings */}
        <div className="bg-white/80 backdrop-blur-sm rounded-3xl border border-slate-200/60 p-6 sm:p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-100 to-cyan-100 flex items-center justify-center">
              <svg className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-800">Storage</h2>
              <p className="text-sm text-slate-500">Local file storage settings</p>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Storage Path</label>
            <input
              name="storage_path"
              value={settings.storage_path}
              onChange={handleSettingsChange}
              className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50/50 text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              placeholder="e.g., recordings, /path/to/recordings"
            />
            <p className="text-xs text-slate-400 mt-2">Directory where audio files will be stored locally</p>
          </div>
        </div>

        {/* Amazon S3 Settings */}
        <div className="bg-white/80 backdrop-blur-sm rounded-3xl border border-slate-200/60 p-6 sm:p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-100 to-amber-100 flex items-center justify-center">
              <svg className="w-5 h-5 text-orange-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-800">Amazon S3</h2>
              <p className="text-sm text-slate-500">Cloud storage configuration</p>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">S3 Bucket Name</label>
            <input
              name="s3_bucket"
              value={settings.s3_bucket}
              onChange={handleSettingsChange}
              className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50/50 text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              placeholder="e.g., my-voice-datasets"
            />
            <p className="text-xs text-slate-400 mt-2">S3 bucket where datasets will be exported</p>
          </div>
        </div>

        {/* Hugging Face Settings */}
        <div className="bg-white/80 backdrop-blur-sm rounded-3xl border border-slate-200/60 p-6 sm:p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-yellow-100 to-orange-100 flex items-center justify-center">
              <svg className="w-5 h-5 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-800">Hugging Face</h2>
              <p className="text-sm text-slate-500">Dataset hub integration</p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">API Token</label>
              <input
                name="huggingface_token"
                value={settings.huggingface_token}
                onChange={handleSettingsChange}
                type="password"
                className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50/50 text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                placeholder="hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Repository</label>
              <input
                name="huggingface_repo"
                value={settings.huggingface_repo}
                onChange={handleSettingsChange}
                className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50/50 text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                placeholder="e.g., username/dataset-name"
              />
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex flex-col sm:flex-row items-center justify-end gap-4">
          {saveMessage && (
            <span className={`text-sm font-medium ${
              saveMessage.includes('successfully') ? 'text-green-600' : 'text-red-600'
            }`}>
              {saveMessage}
            </span>
          )}
          <button
            onClick={saveSettings}
            disabled={isSaving}
            className="w-full sm:w-auto px-8 py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-indigo-200"
          >
            {isSaving ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Saving...
              </span>
            ) : 'Save Settings'}
          </button>
        </div>

        {/* Danger Zone */}
        <div className="bg-red-50/80 backdrop-blur-sm rounded-3xl border border-red-200/60 p-6 sm:p-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-red-100 flex items-center justify-center">
              <svg className="w-5 h-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-bold text-red-800">Danger Zone</h2>
              <p className="text-sm text-red-600">Irreversible actions</p>
            </div>
          </div>

          <p className="text-sm text-red-600 mb-4">
            This will permanently delete all your projects, recordings, settings, and audio files.
          </p>
          <button
            onClick={() => setShowClearModal(true)}
            className="px-6 py-3 rounded-xl font-semibold text-white bg-red-500 hover:bg-red-600 transition-colors"
          >
            Clear All My Data
          </button>
        </div>
      </div>

      {/* Clear Data Confirmation Modal */}
      {showClearModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity" onClick={() => setShowClearModal(false)} />

            <div className="relative bg-white rounded-3xl shadow-2xl w-full max-w-md p-6 sm:p-8 text-center">
              <div className="w-16 h-16 mx-auto rounded-full bg-red-100 flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-slate-800 mb-2">Clear All Data?</h2>
              <p className="text-slate-500 mb-6">
                This action cannot be undone. All your projects, recordings, and settings will be permanently deleted.
              </p>

              <div className="flex gap-3">
                <button
                  onClick={() => setShowClearModal(false)}
                  disabled={isClearing}
                  className="flex-1 px-6 py-3 rounded-xl font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 disabled:opacity-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={clearUserData}
                  disabled={isClearing}
                  className="flex-1 px-6 py-3 rounded-xl font-semibold text-white bg-red-500 hover:bg-red-600 disabled:opacity-50 transition-colors"
                >
                  {isClearing ? 'Clearing...' : 'Yes, Clear Everything'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Settings;
