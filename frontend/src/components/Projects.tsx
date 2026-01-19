import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_BASE, authHeaders, fetchJson } from '../utils/api';
import { useToast } from './Toast';
import ShareModal from './ShareModal';

interface Project {
  id: number;
  name: string;
  is_rtl?: boolean;
  created_at: string;
  total_prompts?: number;
  recorded_count?: number;
  last_recorded_index?: number;
  is_owner?: boolean;
  owner_username?: string;
  collaborator_count?: number;
}

function Projects() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [showProjectModal, setShowProjectModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);
  const [projectToDelete, setProjectToDelete] = useState<Project | null>(null);
  const [projectToShare, setProjectToShare] = useState<Project | null>(null);
  const [projectName, setProjectName] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [multiLineText, setMultiLineText] = useState('');
  const [inputMethod, setInputMethod] = useState<'csv' | 'text'>('csv');
  const [isRtl, setIsRtl] = useState(false);
  const navigate = useNavigate();
  const token = localStorage.getItem('token');
  const { showError, showSuccess } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  useEffect(() => {
    fetchProjects();
  }, [token]);

  const fetchProjects = async () => {
    if (!token) return;
    setIsLoading(true);
    setFetchError(null);
    try {
      const data = await fetchJson<Project[]>(`/api/v1/projects/`, token);
      setProjects(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load projects';
      setFetchError(message);
      showError(message);
      console.error('Failed to load projects', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const createProject = async () => {
    if (!projectName.trim()) {
      showError('Please provide a project name.');
      return;
    }

    if (inputMethod === 'csv' && !selectedFile) {
      showError('Please select a CSV file.');
      return;
    }

    if (inputMethod === 'text' && !multiLineText.trim()) {
      showError('Please enter some prompts.');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('project_name', projectName);
      formData.append('is_rtl', isRtl.toString());
      if (inputMethod === 'csv') {
        formData.append('file', selectedFile!);
      } else {
        formData.append('prompts_text', multiLineText);
      }

      const res = await fetch(`${API_BASE}/api/v1/projects/`, {
        method: 'POST',
        headers: authHeaders(token || undefined),
        body: formData,
      });
      const data = await res.json();

      if (res.ok) {
        showSuccess(`Project "${projectName}" created successfully!`);
        setShowProjectModal(false);
        setProjectName('');
        setSelectedFile(null);
        setMultiLineText('');
        setInputMethod('csv');
        fetchProjects();
        navigate(`/recording/${data.id}`);
      } else {
        showError(data.detail || 'Failed to create project');
      }
    } catch (err) {
      showError('Failed to create project. Please check your connection and try again.');
    }
  };

  const resetModal = () => {
    setShowProjectModal(false);
    setProjectName('');
    setSelectedFile(null);
    setMultiLineText('');
    setInputMethod('csv');
    setIsRtl(false);
  };

  const startRecording = (projectId: number) => {
    navigate(`/recording/${projectId}`);
  };

  const handleDeleteClick = (project: Project, e: React.MouseEvent) => {
    e.stopPropagation();
    setProjectToDelete(project);
    setShowDeleteModal(true);
  };

  const handleShareClick = (project: Project, e: React.MouseEvent) => {
    e.stopPropagation();
    setProjectToShare(project);
    setShowShareModal(true);
  };

  const confirmDelete = async () => {
    if (!projectToDelete) return;

    try {
      const res = await fetch(`${API_BASE}/api/v1/projects/${projectToDelete.id}`, {
        method: 'DELETE',
        headers: authHeaders(token || undefined),
      });

      if (res.ok) {
        showSuccess(`Project "${projectToDelete.name}" deleted successfully`);
        setShowDeleteModal(false);
        setProjectToDelete(null);
        fetchProjects();
      } else {
        const error = await res.json();
        showError(error.detail || 'Failed to delete project');
      }
    } catch (error) {
      showError('Failed to delete project. Please check your connection and try again.');
    }
  };

  const getProgressPercentage = (project: Project) => {
    if (!project.total_prompts || !project.recorded_count) return 0;
    return Math.round((project.recorded_count / project.total_prompts) * 100);
  };

  const getProgressText = (project: Project) => {
    if (!project.total_prompts || !project.recorded_count) return 'No recordings yet';
    return `${project.recorded_count} of ${project.total_prompts} recorded`;
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-800">Your Projects</h1>
          <p className="text-slate-500 mt-1">Manage your voice dataset collections</p>
        </div>
        <button
          onClick={() => setShowProjectModal(true)}
          className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 shadow-lg shadow-indigo-200 transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98]"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Project
        </button>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="flex items-center gap-3 text-slate-500">
            <svg className="w-6 h-6 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <span>Loading projects...</span>
          </div>
        </div>
      )}

      {/* Error State */}
      {fetchError && !isLoading && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-6 text-center">
          <div className="w-12 h-12 mx-auto rounded-full bg-red-100 flex items-center justify-center mb-4">
            <svg className="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-red-800 mb-2">Failed to load projects</h3>
          <p className="text-red-600 mb-4">{fetchError}</p>
          <button
            onClick={fetchProjects}
            className="px-6 py-2 rounded-xl font-medium text-red-600 bg-red-100 hover:bg-red-200 transition-colors"
          >
            Try Again
          </button>
        </div>
      )}

      {!isLoading && !fetchError && projects.length > 0 ? (
        <div className="grid gap-4 sm:gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map(project => (
            <div
              key={project.id}
              className="group relative bg-white/80 backdrop-blur-sm rounded-2xl border border-slate-200/60 p-5 sm:p-6 hover:shadow-xl hover:shadow-indigo-100/50 hover:border-indigo-200 transition-all duration-300 cursor-pointer"
              onClick={() => startRecording(project.id)}
            >
              {/* Action Buttons */}
              <div className="absolute top-4 right-4 flex gap-2 opacity-0 group-hover:opacity-100 transition-all duration-200">
                {/* Share Button - only for owners */}
                {(project.is_owner !== false) && (
                  <button
                    onClick={(e) => handleShareClick(project, e)}
                    className="p-2 rounded-xl bg-indigo-50 text-indigo-500 hover:bg-indigo-100 hover:text-indigo-600"
                    title="Share project"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                    </svg>
                  </button>
                )}
                {/* Delete Button - only for owners */}
                {(project.is_owner !== false) && (
                  <button
                    onClick={(e) => handleDeleteClick(project, e)}
                    className="p-2 rounded-xl bg-red-50 text-red-500 hover:bg-red-100 hover:text-red-600"
                    title="Delete project"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                )}
              </div>

              {/* Project Icon */}
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-100 to-purple-100 flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              </div>

              {/* Project Info */}
              <h3 className="font-bold text-lg text-slate-800 mb-1 pr-8 truncate">{project.name}</h3>
              <div className="flex flex-wrap items-center gap-2 mb-4">
                <p className="text-slate-400 text-sm">
                  {new Date(project.created_at).toLocaleDateString()}
                </p>
                {project.is_rtl && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                    RTL
                  </span>
                )}
                {/* Shared badge - show if project has collaborators */}
                {(project.is_owner !== false) && project.collaborator_count && project.collaborator_count > 0 && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-700">
                    Shared ({project.collaborator_count})
                  </span>
                )}
                {/* Shared by badge - show if user is not owner */}
                {project.is_owner === false && project.owner_username && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                    By {project.owner_username}
                  </span>
                )}
              </div>

              {/* Progress */}
              <div className="mb-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs font-medium text-slate-500">Progress</span>
                  <span className="text-xs font-medium text-indigo-600">{getProgressPercentage(project)}%</span>
                </div>
                <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-500"
                    style={{ width: `${getProgressPercentage(project)}%` }}
                  />
                </div>
                <p className="text-xs text-slate-400 mt-1">{getProgressText(project)}</p>
              </div>

              {/* Action Button */}
              <button className="w-full py-2.5 px-4 rounded-xl font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 transition-colors duration-200 flex items-center justify-center gap-2">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {project.recorded_count && project.recorded_count > 0 ? 'Continue' : 'Start Recording'}
              </button>
            </div>
          ))}
        </div>
      ) : !isLoading && !fetchError ? (
        <div className="bg-white/80 backdrop-blur-sm rounded-3xl border border-slate-200/60 p-8 sm:p-12 text-center">
          <div className="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-indigo-100 to-purple-100 flex items-center justify-center mb-6">
            <svg className="w-10 h-10 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-800 mb-2">No projects yet</h2>
          <p className="text-slate-500 mb-8 max-w-md mx-auto">Create your first voice dataset project to start collecting recordings</p>
          <button
            onClick={() => setShowProjectModal(true)}
            className="inline-flex items-center gap-2 px-8 py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 shadow-lg shadow-indigo-200 transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98]"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Create First Project
          </button>
        </div>
      ) : null}

      {/* Create Project Modal */}
      {showProjectModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20">
            <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity" onClick={resetModal} />

            <div className="relative bg-white rounded-3xl shadow-2xl w-full max-w-lg p-6 sm:p-8 overflow-hidden">
              {/* Modal Header */}
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl sm:text-2xl font-bold text-slate-800">Create New Project</h2>
                <button
                  onClick={resetModal}
                  className="p-2 rounded-xl hover:bg-slate-100 transition-colors"
                >
                  <svg className="w-5 h-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="space-y-5">
                {/* Project Name */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Project Name</label>
                  <input
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50/50 text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                    placeholder="Enter project name"
                  />
                </div>

                {/* Input Method */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-3">Input Method</label>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      type="button"
                      onClick={() => setInputMethod('csv')}
                      className={`p-4 rounded-xl border-2 transition-all text-left ${
                        inputMethod === 'csv'
                          ? 'border-indigo-500 bg-indigo-50'
                          : 'border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      <svg className={`w-6 h-6 mb-2 ${inputMethod === 'csv' ? 'text-indigo-600' : 'text-slate-400'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <span className={`font-medium ${inputMethod === 'csv' ? 'text-indigo-700' : 'text-slate-600'}`}>CSV Upload</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setInputMethod('text')}
                      className={`p-4 rounded-xl border-2 transition-all text-left ${
                        inputMethod === 'text'
                          ? 'border-indigo-500 bg-indigo-50'
                          : 'border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      <svg className={`w-6 h-6 mb-2 ${inputMethod === 'text' ? 'text-indigo-600' : 'text-slate-400'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h7" />
                      </svg>
                      <span className={`font-medium ${inputMethod === 'text' ? 'text-indigo-700' : 'text-slate-600'}`}>Text Input</span>
                    </button>
                  </div>
                </div>

                {/* RTL Toggle */}
                <div className="flex items-center justify-between p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <div>
                    <p className="font-medium text-slate-700">Right-to-Left (RTL)</p>
                    <p className="text-sm text-slate-500">For Arabic, Persian, Hebrew, etc.</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setIsRtl(!isRtl)}
                    className={`relative w-12 h-7 rounded-full transition-colors ${isRtl ? 'bg-indigo-500' : 'bg-slate-300'}`}
                  >
                    <span className={`absolute top-1 left-1 w-5 h-5 bg-white rounded-full shadow transition-transform ${isRtl ? 'translate-x-5' : ''}`} />
                  </button>
                </div>

                {/* CSV Upload */}
                {inputMethod === 'csv' && (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">CSV File with Prompts</label>
                    <div className="relative">
                      <input
                        type="file"
                        accept=".csv"
                        onChange={handleFileSelect}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                      />
                      <div className={`p-6 border-2 border-dashed rounded-xl text-center transition-colors ${
                        selectedFile ? 'border-green-300 bg-green-50' : 'border-slate-300 hover:border-indigo-300 hover:bg-indigo-50/50'
                      }`}>
                        {selectedFile ? (
                          <div className="flex items-center justify-center gap-2 text-green-600">
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                            <span className="font-medium">{selectedFile.name}</span>
                          </div>
                        ) : (
                          <>
                            <svg className="w-8 h-8 mx-auto text-slate-400 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                            </svg>
                            <p className="text-sm text-slate-500">Click to upload CSV file</p>
                          </>
                        )}
                      </div>
                    </div>
                    <p className="text-xs text-slate-400 mt-2">One prompt per row in the CSV file</p>
                  </div>
                )}

                {/* Text Input */}
                {inputMethod === 'text' && (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">Prompts (one per line)</label>
                    <textarea
                      value={multiLineText}
                      onChange={(e) => setMultiLineText(e.target.value)}
                      className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50/50 text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all resize-none"
                      placeholder="Enter your prompts here, one per line..."
                      rows={6}
                      style={{
                        direction: isRtl ? 'rtl' : 'ltr',
                        textAlign: isRtl ? 'right' : 'left'
                      }}
                    />
                    {multiLineText && (
                      <div className="flex items-center gap-2 mt-2 text-sm text-indigo-600">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                        </svg>
                        {multiLineText.split('\n').filter(line => line.trim()).length} prompts detected
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Modal Footer */}
              <div className="flex flex-col-reverse sm:flex-row gap-3 mt-8">
                <button
                  onClick={resetModal}
                  className="flex-1 px-6 py-3 rounded-xl font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={createProject}
                  disabled={!projectName.trim() || (inputMethod === 'csv' && !selectedFile) || (inputMethod === 'text' && !multiLineText.trim())}
                  className="flex-1 px-6 py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-indigo-200"
                >
                  Create Project
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && projectToDelete && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity" onClick={() => { setShowDeleteModal(false); setProjectToDelete(null); }} />

            <div className="relative bg-white rounded-3xl shadow-2xl w-full max-w-md p-6 sm:p-8 text-center">
              <div className="w-16 h-16 mx-auto rounded-full bg-red-100 flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-slate-800 mb-2">Delete Project?</h2>
              <p className="text-slate-500 mb-6">
                Are you sure you want to delete <strong className="text-slate-700">"{projectToDelete.name}"</strong>?
                This will permanently delete all recordings.
              </p>

              <div className="flex gap-3">
                <button
                  onClick={() => { setShowDeleteModal(false); setProjectToDelete(null); }}
                  className="flex-1 px-6 py-3 rounded-xl font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmDelete}
                  className="flex-1 px-6 py-3 rounded-xl font-semibold text-white bg-red-500 hover:bg-red-600 transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Share Modal */}
      {projectToShare && (
        <ShareModal
          projectId={projectToShare.id}
          projectName={projectToShare.name}
          isOpen={showShareModal}
          onClose={() => {
            setShowShareModal(false);
            setProjectToShare(null);
            fetchProjects(); // Refresh to update collaborator counts
          }}
          token={token}
        />
      )}
    </div>
  );
}

export default Projects;
