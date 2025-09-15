import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const BACKEND_URL = 'http://localhost:8500';
interface Project {
  id: number;
  name: string;
  is_rtl?: boolean;
  created_at: string;
  total_prompts?: number;
  recorded_count?: number;
  last_recorded_index?: number;
}

function Projects() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [showProjectModal, setShowProjectModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [projectToDelete, setProjectToDelete] = useState<Project | null>(null);
  const [projectName, setProjectName] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [multiLineText, setMultiLineText] = useState('');
  const [inputMethod, setInputMethod] = useState<'csv' | 'text'>('csv');
  const [isRtl, setIsRtl] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    const res = await fetch(`${BACKEND_URL}/projects/`);
    const data = await res.json();
    console.log('Projects data received:', data.projects);
    setProjects(data.projects);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const createProject = async () => {
    if (!projectName.trim()) {
      alert('Please provide a project name.');
      return;
    }

    if (inputMethod === 'csv' && !selectedFile) {
      alert('Please select a CSV file.');
      return;
    }

    if (inputMethod === 'text' && !multiLineText.trim()) {
      alert('Please enter some prompts.');
      return;
    }

    try {
      let res;
      
      if (inputMethod === 'csv') {
        const formData = new FormData();
        formData.append('file', selectedFile!);
        formData.append('project_name', projectName);
        formData.append('is_rtl', isRtl.toString());
        
        res = await fetch(`${BACKEND_URL}/upload_csv/`, {
          method: 'POST',
          body: formData,
        });
      } else {
        const formData = new FormData();
        formData.append('project_name', projectName);
        formData.append('prompts_text', multiLineText);
        formData.append('is_rtl', isRtl.toString());
        
        res = await fetch(`${BACKEND_URL}/create_project/`, {
          method: 'POST',
          body: formData,
        });
      }
      if (res.ok) {
        const data = await res.json();
        setShowProjectModal(false);
        setProjectName('');
        setSelectedFile(null);
        setMultiLineText('');
        setInputMethod('csv');
        fetchProjects();
        // Navigate to the new project
        navigate(`/recording/${data.project_id}`);
      } else {
        const error = await res.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (res) {
      alert('Failed to create project. Please try again. response: ' + res);
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

  const confirmDelete = async () => {
    if (!projectToDelete) return;
    
    try {
      const res = await fetch(`${BACKEND_URL}/projects/${projectToDelete.id}`, {
        method: 'DELETE',
      });
      
      if (res.ok) {
        setShowDeleteModal(false);
        setProjectToDelete(null);
        fetchProjects();
      } else {
        const error = await res.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      alert('Failed to delete project. Please try again.');
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
    <div className="max-w-4xl mx-auto px-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Projects</h1>
          <button 
            onClick={() => setShowProjectModal(true)} 
            className="bg-gray-900 text-white rounded-lg px-6 py-3 font-semibold hover:bg-gray-800 transition shadow-sm"
          >
            New Project
          </button>
        </div>

        {projects.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {projects.map(project => (
              <div 
                key={project.id} 
                className="border border-gray-200 rounded-lg p-6 hover:border-gray-300 hover:shadow-md transition cursor-pointer relative group"
                onClick={() => startRecording(project.id)}
              >
                {/* Delete Button */}
                <button
                  onClick={(e) => handleDeleteClick(project, e)}
                  className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity bg-red-50 text-red-600 rounded-full p-2 hover:bg-red-100"
                  title="Delete project"
                >
                  🗑️
                </button>

                <h3 className="font-bold text-lg text-gray-900 mb-2 pr-8">{project.name}</h3>
                <div className="flex items-center gap-2 mb-4">
                  <p className="text-gray-500 text-sm">
                    Created: {new Date(project.created_at).toLocaleDateString()}
                  </p>
                  {project.is_rtl && (
                    <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                      RTL
                    </span>
                  )}
                </div>

                {/* Progress Bar */}
                <div className="mb-4">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs font-medium text-gray-600">Progress</span>
                    <span className="text-xs text-gray-500">{getProgressText(project)}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-gray-900 h-2 rounded-full transition-all duration-300" 
                      style={{ width: `${getProgressPercentage(project)}%` }}
                    ></div>
                  </div>
                </div>

                <button className="w-full bg-gray-900 text-white rounded-lg px-4 py-2 font-semibold hover:bg-gray-800 transition">
                  {project.recorded_count && project.recorded_count > 0 ? 'Continue Recording' : 'Start Recording'}
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🎤</div>
            <h2 className="text-2xl font-bold text-gray-700 mb-2">No projects yet</h2>
            <p className="text-gray-500 mb-6">Create your first voice dataset project to get started!</p>
            <button 
              onClick={() => setShowProjectModal(true)} 
              className="bg-gray-900 text-white rounded-lg px-8 py-3 font-semibold hover:bg-gray-800 transition shadow-sm"
            >
              Create First Project
            </button>
          </div>
        )}

        {/* Project Creation Modal */}
        {showProjectModal && (
          <div className="fixed top-0 left-0 w-screen h-screen bg-black/60 z-40 flex items-center justify-center">
            <div className="bg-white p-8 rounded-lg min-w-[500px] max-w-[600px] shadow-lg max-h-[90vh] overflow-y-auto">
              <h2 className="font-bold text-xl text-gray-900 mb-6">Create New Project</h2>
              
              <div className="space-y-4">
                <label className="block">
                  <span className="text-gray-700 font-medium">Project Name</span>
                  <input 
                    value={projectName} 
                    onChange={(e) => setProjectName(e.target.value)} 
                    className="w-full border border-gray-300 rounded-lg px-4 py-3 text-base bg-gray-50 text-gray-900 outline-none mt-1 focus:border-gray-500" 
                    placeholder="Enter project name"
                  />
                </label>
                
                {/* Input Method Selection */}
                <div className="block">
                  <span className="text-gray-700 font-medium">Input Method</span>
                  <div className="flex gap-4 mt-2">
                    <label className="flex items-center">
                      <input 
                        type="radio" 
                        name="inputMethod" 
                        value="csv" 
                        checked={inputMethod === 'csv'} 
                        onChange={(e) => setInputMethod(e.target.value as 'csv' | 'text')}
                        className="mr-2"
                      />
                      <span className="text-gray-700">CSV Upload</span>
                    </label>
                    <label className="flex items-center">
                      <input 
                        type="radio" 
                        name="inputMethod" 
                        value="text" 
                        checked={inputMethod === 'text'} 
                        onChange={(e) => setInputMethod(e.target.value as 'csv' | 'text')}
                        className="mr-2"
                      />
                      <span className="text-gray-700">Multi-line Text</span>
                    </label>
                  </div>
                </div>
                
                {/* RTL Option */}
                <div className="block">
                  <label className="flex items-center">
                    <input 
                      type="checkbox" 
                      checked={isRtl} 
                      onChange={(e) => setIsRtl(e.target.checked)}
                      className="mr-2"
                    />
                    <span className="text-gray-700 font-medium">Right-to-Left (RTL) Language</span>
                  </label>
                  <p className="text-sm text-gray-500 mt-1 ml-6">
                    Enable for Arabic, Persian, or other RTL languages
                  </p>
                </div>
                
                {/* CSV Upload Section */}
                {inputMethod === 'csv' && (
                  <label className="block">
                    <span className="text-gray-700 font-medium">CSV File with Prompts</span>
                    <input 
                      type="file" 
                      accept=".csv" 
                      onChange={handleFileSelect} 
                      className="w-full border border-gray-300 rounded-lg px-4 py-3 text-base bg-gray-50 text-gray-900 outline-none mt-1 focus:border-gray-500" 
                    />
                    {selectedFile && (
                      <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded text-sm text-green-700">
                        ✓ Selected: {selectedFile.name}
                      </div>
                    )}
                    <p className="text-sm text-gray-500 mt-1">Upload a CSV file with one prompt per row</p>
                  </label>
                )}
                
                {/* Multi-line Text Section */}
                {inputMethod === 'text' && (
                  <label className="block">
                    <span className="text-gray-700 font-medium">Prompts (one per line)</span>
                    <textarea 
                      value={multiLineText} 
                      onChange={(e) => setMultiLineText(e.target.value)} 
                      className="w-full border border-gray-300 rounded-lg px-4 py-3 text-base bg-gray-50 text-gray-900 outline-none mt-1 focus:border-gray-500 resize-vertical" 
                      placeholder="Enter your prompts here, one per line..."
                      rows={8}
                      style={{ 
                        direction: isRtl ? 'rtl' : 'ltr',
                        textAlign: isRtl ? 'right' : 'left'
                      }}
                    />
                    <p className="text-sm text-gray-500 mt-1">
                      Enter each prompt on a separate line. Empty lines will be ignored.
                    </p>
                    {multiLineText && (
                      <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded text-sm text-blue-700">
                        ✓ {multiLineText.split('\n').filter(line => line.trim()).length} prompts detected
                      </div>
                    )}
                  </label>
                )}
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <button 
                  onClick={resetModal} 
                  className="bg-gray-100 text-gray-600 rounded-lg px-5 py-2 font-semibold hover:bg-gray-200 transition"
                >
                  Cancel
                </button>
                <button 
                  onClick={createProject}
                  className="bg-gray-900 text-white rounded-lg px-5 py-2 font-semibold hover:bg-gray-800 transition disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={
                    !projectName.trim() || 
                    (inputMethod === 'csv' && !selectedFile) || 
                    (inputMethod === 'text' && !multiLineText.trim())
                  }
                >
                  Create Project
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {showDeleteModal && projectToDelete && (
          <div className="fixed top-0 left-0 w-screen h-screen bg-black/60 z-40 flex items-center justify-center">
            <div className="bg-white p-8 rounded-lg min-w-[400px] shadow-lg">
              <h2 className="font-bold text-xl text-red-600 mb-4">Delete Project</h2>
              <p className="text-gray-700 mb-6">
                Are you sure you want to delete <strong>"{projectToDelete.name}"</strong>? 
                This will permanently delete the project and all its recordings.
              </p>
              
              <div className="flex justify-end gap-3">
                <button 
                  onClick={() => { setShowDeleteModal(false); setProjectToDelete(null); }} 
                  className="bg-gray-100 text-gray-600 rounded-lg px-5 py-2 font-semibold hover:bg-gray-200 transition"
                >
                  Cancel
                </button>
                <button 
                  onClick={confirmDelete}
                  className="bg-red-600 text-white rounded-lg px-5 py-2 font-semibold hover:bg-red-700 transition"
                >
                  Delete Project
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Projects; 