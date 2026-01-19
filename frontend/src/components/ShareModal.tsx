import React, { useState, useEffect } from 'react';
import { API_BASE, authHeaders } from '../utils/api';
import { useToast } from './Toast';

interface Collaborator {
  id: number;
  user_id: number;
  username: string;
  email: string;
  added_at: string;
}

interface ShareModalProps {
  projectId: number;
  projectName: string;
  isOpen: boolean;
  onClose: () => void;
  token: string | null;
}

function ShareModal({ projectId, projectName, isOpen, onClose, token }: ShareModalProps) {
  const [emailOrUsername, setEmailOrUsername] = useState('');
  const [collaborators, setCollaborators] = useState<Collaborator[]>([]);
  const [isOwner, setIsOwner] = useState(true);
  const [loading, setLoading] = useState(false);
  const [fetchingCollabs, setFetchingCollabs] = useState(false);
  const { showError, showSuccess } = useToast();

  useEffect(() => {
    if (isOpen && projectId) {
      fetchCollaborators();
    }
  }, [isOpen, projectId]);

  const fetchCollaborators = async () => {
    if (!token) return;
    setFetchingCollabs(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/collaborators`, {
        headers: authHeaders(token),
      });

      if (!res.ok) {
        const data = await res.json();
        showError(data.detail || 'Failed to load collaborators');
        return;
      }

      const data = await res.json();
      setCollaborators(data.collaborators || []);
      setIsOwner(data.is_owner);
    } catch (err) {
      showError('Failed to load collaborators. Please check your connection.');
      console.error('Failed to fetch collaborators', err);
    } finally {
      setFetchingCollabs(false);
    }
  };

  const handleShare = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!emailOrUsername.trim() || !token) return;

    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('email_or_username', emailOrUsername.trim());

      const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/share`, {
        method: 'POST',
        headers: authHeaders(token),
        body: formData,
      });

      const data = await res.json();

      if (res.ok) {
        showSuccess(`Project shared with ${data.collaborator.username}`);
        setEmailOrUsername('');
        fetchCollaborators();
      } else {
        showError(data.detail || 'Failed to share project');
      }
    } catch (err) {
      showError('Failed to share project. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveCollaborator = async (userId: number, username: string) => {
    if (!token) return;
    if (!confirm(`Remove ${username} from this project?`)) return;

    try {
      const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/collaborators/${userId}`, {
        method: 'DELETE',
        headers: authHeaders(token),
      });

      if (res.ok) {
        showSuccess(`${username} removed from project`);
        fetchCollaborators();
      } else {
        const data = await res.json();
        showError(data.detail || 'Failed to remove collaborator');
      }
    } catch (err) {
      showError('Failed to remove collaborator. Please try again.');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity" onClick={onClose} />

        <div className="relative bg-white rounded-3xl shadow-2xl w-full max-w-lg p-6 sm:p-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl sm:text-2xl font-bold text-slate-800">Share Project</h2>
              <p className="text-slate-500 text-sm mt-1">{projectName}</p>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-xl hover:bg-slate-100 transition-colors"
            >
              <svg className="w-5 h-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Share Form - Only show if owner */}
          {isOwner && (
            <form onSubmit={handleShare} className="mb-6">
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Share with user (email or username)
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={emailOrUsername}
                  onChange={(e) => setEmailOrUsername(e.target.value)}
                  className="flex-1 px-4 py-3 rounded-xl border border-slate-200 bg-slate-50/50 text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                  placeholder="Enter email or username"
                />
                <button
                  type="submit"
                  disabled={loading || !emailOrUsername.trim()}
                  className="px-6 py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-indigo-200"
                >
                  {loading ? (
                    <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                  ) : (
                    'Share'
                  )}
                </button>
              </div>
            </form>
          )}

          {/* Collaborators List */}
          <div>
            <h3 className="text-sm font-medium text-slate-700 mb-3">
              {fetchingCollabs ? 'Loading...' : collaborators.length > 0 ? `Shared with (${collaborators.length})` : 'Not shared with anyone yet'}
            </h3>

            {fetchingCollabs ? (
              <div className="flex items-center justify-center py-8">
                <svg className="w-6 h-6 animate-spin text-indigo-500" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              </div>
            ) : collaborators.length > 0 ? (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {collaborators.map((collab) => (
                  <div
                    key={collab.id}
                    className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white font-semibold">
                        {collab.username.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <p className="font-medium text-slate-800">{collab.username}</p>
                        <p className="text-sm text-slate-500">{collab.email}</p>
                      </div>
                    </div>
                    {isOwner && (
                      <button
                        onClick={() => handleRemoveCollaborator(collab.user_id, collab.username)}
                        className="p-2 rounded-lg text-red-500 hover:bg-red-50 transition-colors"
                        title="Remove collaborator"
                      >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-slate-400">
                <svg className="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                <p>No collaborators yet</p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="mt-6 pt-4 border-t border-slate-200">
            <button
              onClick={onClose}
              className="w-full px-6 py-3 rounded-xl font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ShareModal;
