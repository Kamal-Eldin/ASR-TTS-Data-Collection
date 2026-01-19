import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { encodeWAV, mergeBuffers, createAudioContext } from '../utils/wavEncoder';
import { API_BASE, authHeaders, fetchJson } from '../utils/api';

interface Project {
  id: number;
  name: string;
  is_rtl?: boolean;
  created_at: string;
}

interface Prompt {
  id: number;
  text: string;
  order_index: number;
}

interface RecordingEntry {
  filename: string;
  prompt_id?: number;
  text?: string;
  recorded_at?: string;
}

function Recording() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const token = localStorage.getItem('token');

  const [project, setProject] = useState<Project | null>(null);
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [existingRecordings, setExistingRecordings] = useState<Record<number, RecordingEntry>>({});
  const [isRecording, setIsRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [exporting, setExporting] = useState<null | 's3' | 'hf'>(null);
  const [exportMessage, setExportMessage] = useState<string | null>(null);
  const [showAddPromptsModal, setShowAddPromptsModal] = useState(false);
  const [addPromptsText, setAddPromptsText] = useState('');
  const [addPromptsFile, setAddPromptsFile] = useState<File | null>(null);
  const [addPromptsMethod, setAddPromptsMethod] = useState<'csv' | 'text'>('text');
  const [isAddingPrompts, setIsAddingPrompts] = useState(false);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const audioBuffers = useRef<Float32Array[]>([]);
  const isRecordingRef = useRef<boolean>(false);

  const currentPrompt = prompts[currentIdx];

  const loadData = useCallback(async () => {
    if (!projectId || !token) return;
    try {
      const proj = await fetchJson<Project>(`/api/v1/projects/${projectId}`, token);
      const promptList = await fetchJson<Prompt[]>(`/api/v1/projects/${projectId}/prompts`, token);
      const recordingsResponse = await fetch(`${API_BASE}/api/v1/projects/${projectId}/recordings`, {
        headers: authHeaders(token),
      });
      const recBody = await recordingsResponse.json();
      const recList: RecordingEntry[] = Array.isArray(recBody) ? recBody : recBody.recordings || [];

      setProject(proj);
      setPrompts(promptList.sort((a, b) => a.order_index - b.order_index));

      const map: Record<number, RecordingEntry> = {};
      recList.forEach((r) => {
        if (r.prompt_id) map[r.prompt_id] = r;
      });
      setExistingRecordings(map);
      setCurrentIdx(0);
    } catch (err) {
      console.error('Failed to load project data', err);
      navigate('/');
    }
  }, [projectId, token, navigate]);

  useEffect(() => {
    loadData();
    return () => {
      if (audioContextRef.current) audioContextRef.current.close();
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
    };
  }, [loadData]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Enter') {
        if (!isRecording) startRecording();
        else stopRecording();
      } else if (e.key === 'ArrowLeft') {
        nextPrompt();
      } else if (e.key === 'ArrowRight') {
        prevPrompt();
      } else if (e.key === ' ') {
        e.preventDefault();
        playOrStop();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [isRecording, currentIdx, audioUrl, prompts]);

  const startRecording = async () => {
    if (!navigator.mediaDevices || !currentPrompt) return alert('No prompt selected');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 48000,
          sampleSize: 16,
          echoCancellation: false,
          noiseSuppression: false,
          autoGainControl: false,
        },
      });
      streamRef.current = stream;

      if (!audioContextRef.current) audioContextRef.current = createAudioContext();

      const audioContext = audioContextRef.current;
      const source = audioContext.createMediaStreamSource(stream);
      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      sourceRef.current = source;
      processorRef.current = processor;
      audioBuffers.current = [];

      processor.onaudioprocess = (e) => {
        if (!isRecordingRef.current) return;
        const inputData = e.inputBuffer.getChannelData(0);
        const buffer = new Float32Array(inputData.length);
        buffer.set(inputData);
        audioBuffers.current.push(buffer);
      };

      source.connect(processor);
      processor.connect(audioContext.destination);

      isRecordingRef.current = true;
      setIsRecording(true);
    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Failed to access microphone. Please check permissions.');
    }
  };

  const stopRecording = async () => {
    if (!isRecording || !audioContextRef.current || !currentPrompt || !project || !token) return;
    isRecordingRef.current = false;
    setIsRecording(false);
    if (sourceRef.current && processorRef.current) {
      sourceRef.current.disconnect();
      processorRef.current.disconnect();
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
    }

    if (isUploading) return;
    setIsUploading(true);

    try {
      const mergedBuffer = mergeBuffers(audioBuffers.current);
      const sampleRate = audioContextRef.current.sampleRate;
      const wavBlob = encodeWAV(mergedBuffer, sampleRate);
      const url = URL.createObjectURL(wavBlob);
      setAudioUrl(url);

      const formData = new FormData();
      formData.append('text', currentPrompt.text);
      formData.append('audio', new File([wavBlob], 'recording.wav', { type: 'audio/wav' }));
      formData.append('project_id', project.id.toString());

      const response = await fetch(`${API_BASE}/api/v1/recordings/upload_audio/`, {
        method: 'POST',
        headers: authHeaders(token),
        body: formData,
      });

      if (response.ok) {
        await loadData();
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Failed to upload recording');
      }
    } catch (error) {
      console.error('Error stopping recording:', error);
      alert('Failed to upload recording');
    } finally {
      setIsUploading(false);
      audioBuffers.current = [];
    }
  };

  const fetchExistingAudio = async (entry: RecordingEntry) => {
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/recordings/${entry.filename}`, {
        headers: authHeaders(token),
      });
      if (!res.ok) throw new Error('Failed to fetch audio');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      setAudioUrl(url);
    } catch (err) {
      console.error('Unable to fetch audio', err);
    }
  };

  useEffect(() => {
    if (!currentPrompt) return;
    setAudioUrl(null);
    const existing = existingRecordings[currentPrompt.id];
    if (existing) {
      fetchExistingAudio(existing);
    }
  }, [currentIdx, currentPrompt, existingRecordings]);

  const deleteRecording = async () => {
    if (!project || !currentPrompt || !token) return;
    const formData = new FormData();
    formData.append('text', currentPrompt.text);
    formData.append('project_id', project.id.toString());

    try {
      const res = await fetch(`${API_BASE}/api/v1/recordings/delete_audio/`, {
        method: 'POST',
        headers: authHeaders(token),
        body: formData,
      });
      if (!res.ok) {
        const data = await res.json();
        alert(data.detail || 'Failed to delete recording');
        return;
      }
      await loadData();
      setAudioUrl(null);
    } catch (err) {
      alert('Failed to delete recording');
    }
  };

  const playOrStop = () => {
    if (!audioUrl || !audioRef.current) return;
    if (audioRef.current.paused) audioRef.current.play();
    else audioRef.current.pause();
  };

  const nextPrompt = () => {
    setCurrentIdx((idx) => (idx + 1 < prompts.length ? idx + 1 : idx));
  };

  const prevPrompt = () => {
    setCurrentIdx((idx) => (idx - 1 >= 0 ? idx - 1 : idx));
  };

  const exportDataset = async (type: 's3' | 'hf') => {
    if (!project || !token) return;
    setExporting(type);
    setExportMessage(null);
    try {
      if (type === 'hf') {
        const formData = new FormData();
        formData.append('project_id', project.id.toString());
        const res = await fetchJson(`/api/v1/exports/export_hf/`, token, {
          method: 'POST',
          body: formData,
        });
        setExportMessage(res.detail || res.message || 'Export triggered');
      } else {
        const res = await fetchJson(`/api/v1/exports/export_s3/`, token, {
          method: 'POST',
          body: JSON.stringify({ project_id: project.id }),
          headers: authHeaders(token, { 'Content-Type': 'application/json' }),
        });
        setExportMessage(res.detail || res.message || 'Export triggered');
      }
    } catch (err: any) {
      setExportMessage(err.message || 'Export failed');
    } finally {
      setExporting(null);
    }
  };

  const progressPercentage = prompts.length > 0
    ? Math.round((Object.keys(existingRecordings).length / prompts.length) * 100)
    : 0;

  const addPrompts = async () => {
    if (!project || !token) return;

    if (addPromptsMethod === 'text' && !addPromptsText.trim()) {
      alert('Please enter some prompts.');
      return;
    }
    if (addPromptsMethod === 'csv' && !addPromptsFile) {
      alert('Please select a CSV file.');
      return;
    }

    setIsAddingPrompts(true);
    try {
      const formData = new FormData();
      if (addPromptsMethod === 'csv' && addPromptsFile) {
        formData.append('file', addPromptsFile);
      } else {
        formData.append('prompts_text', addPromptsText);
      }

      const res = await fetch(`${API_BASE}/api/v1/projects/${project.id}/prompts`, {
        method: 'POST',
        headers: authHeaders(token),
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        alert(`Added ${data.count} prompts!`);
        setShowAddPromptsModal(false);
        setAddPromptsText('');
        setAddPromptsFile(null);
        await loadData();
      } else {
        const error = await res.json();
        alert(error.detail || 'Failed to add prompts');
      }
    } catch (err) {
      alert('Failed to add prompts. Please try again.');
    } finally {
      setIsAddingPrompts(false);
    }
  };

  const resetAddPromptsModal = () => {
    setShowAddPromptsModal(false);
    setAddPromptsText('');
    setAddPromptsFile(null);
    setAddPromptsMethod('text');
  };

  if (!project || !currentPrompt) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white/80 backdrop-blur-sm rounded-3xl border border-slate-200/60 p-8 text-center">
          <div className="animate-pulse flex flex-col items-center gap-4">
            <div className="w-12 h-12 bg-slate-200 rounded-xl"></div>
            <div className="h-4 w-32 bg-slate-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/')}
            className="p-2 rounded-xl hover:bg-white/80 transition-colors"
          >
            <svg className="w-5 h-5 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-slate-800">{project.name}</h1>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-sm text-slate-500">Prompt {currentIdx + 1} of {prompts.length}</span>
              <span className="text-slate-300">|</span>
              <span className="text-sm text-indigo-600 font-medium">{progressPercentage}% complete</span>
            </div>
          </div>
        </div>
        <button
          onClick={() => setShowAddPromptsModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Recordings
        </button>
      </div>

      {/* Main Recording Area */}
      <div className="bg-white/80 backdrop-blur-sm rounded-3xl border border-slate-200/60 p-6 sm:p-8 mb-6">
        {/* Progress Bar */}
        <div className="mb-6">
          <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-500"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        </div>

        {/* Prompt Display */}
        <div
          className="text-lg sm:text-xl md:text-2xl text-slate-700 bg-gradient-to-br from-slate-50 to-indigo-50/50 rounded-2xl p-6 sm:p-8 mb-6 min-h-[120px] flex items-center justify-center leading-relaxed"
          style={{
            direction: project?.is_rtl ? 'rtl' : 'ltr',
            textAlign: project?.is_rtl ? 'right' : 'left'
          }}
        >
          {currentPrompt.text}
        </div>

        {/* Recording Controls */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4 mb-6">
          <button
            onClick={prevPrompt}
            disabled={currentIdx === 0}
            className="w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-3 rounded-xl font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            <span className="hidden sm:inline">Previous</span>
          </button>

          <button
            onClick={isRecording ? stopRecording : startRecording}
            disabled={isUploading}
            className={`w-full sm:w-auto flex items-center justify-center gap-3 px-8 py-4 rounded-2xl font-semibold text-lg shadow-lg transition-all transform hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed ${
              isRecording
                ? 'bg-red-500 text-white shadow-red-200 animate-pulse'
                : isUploading
                ? 'bg-amber-500 text-white shadow-amber-200'
                : 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-indigo-200'
            }`}
          >
            {isRecording ? (
              <>
                <span className="w-4 h-4 bg-white rounded-sm animate-pulse"></span>
                Stop Recording
              </>
            ) : isUploading ? (
              <>
                <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Uploading...
              </>
            ) : (
              <>
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
                Start Recording
              </>
            )}
          </button>

          <button
            onClick={nextPrompt}
            disabled={currentIdx === prompts.length - 1}
            className="w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-3 rounded-xl font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            <span className="hidden sm:inline">Next</span>
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        {/* Keyboard Shortcuts */}
        <div className="hidden sm:flex items-center justify-center gap-6 text-xs text-slate-400">
          <span><kbd className="px-2 py-1 bg-slate-100 rounded text-slate-500">Enter</kbd> Record</span>
          <span><kbd className="px-2 py-1 bg-slate-100 rounded text-slate-500">Space</kbd> Play</span>
          <span><kbd className="px-2 py-1 bg-slate-100 rounded text-slate-500">&larr;</kbd><kbd className="px-2 py-1 bg-slate-100 rounded text-slate-500 ml-1">&rarr;</kbd> Navigate</span>
        </div>

        {/* Audio Player */}
        {audioUrl && (
          <div className="mt-6 p-4 bg-slate-50 rounded-2xl">
            <div className="flex flex-col sm:flex-row items-center gap-4">
              <audio ref={audioRef} src={audioUrl} controls className="w-full sm:flex-1 rounded-lg" />
              <div className="flex gap-2">
                <button
                  onClick={playOrStop}
                  className="p-3 rounded-xl bg-indigo-100 text-indigo-600 hover:bg-indigo-200 transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </button>
                <button
                  onClick={deleteRecording}
                  className="p-3 rounded-xl bg-red-50 text-red-500 hover:bg-red-100 transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Prompts List */}
      <div className="bg-white/80 backdrop-blur-sm rounded-3xl border border-slate-200/60 p-6 sm:p-8 mb-6">
        <h3 className="font-bold text-slate-800 mb-4">All Prompts</h3>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {prompts.map((p, idx) => {
            const rec = existingRecordings[p.id];
            const isActive = idx === currentIdx;
            return (
              <button
                key={p.id}
                onClick={() => setCurrentIdx(idx)}
                className={`w-full flex items-center justify-between p-3 rounded-xl text-left transition-all ${
                  isActive
                    ? 'bg-indigo-100 border-2 border-indigo-300'
                    : 'bg-slate-50 border-2 border-transparent hover:bg-slate-100'
                }`}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <span className={`flex-shrink-0 w-6 h-6 rounded-full text-xs font-medium flex items-center justify-center ${
                    isActive ? 'bg-indigo-500 text-white' : 'bg-slate-200 text-slate-600'
                  }`}>
                    {idx + 1}
                  </span>
                  <span
                    className="text-sm text-slate-700 truncate"
                    style={{ direction: project.is_rtl ? 'rtl' : 'ltr' }}
                  >
                    {p.text}
                  </span>
                </div>
                {rec ? (
                  <span className="flex-shrink-0 ml-2 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                    Recorded
                  </span>
                ) : (
                  <span className="flex-shrink-0 ml-2 px-2 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-500">
                    Pending
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Export Section */}
      <div className="bg-white/80 backdrop-blur-sm rounded-3xl border border-slate-200/60 p-6 sm:p-8">
        <h3 className="font-bold text-slate-800 mb-4">Export Dataset</h3>
        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={() => exportDataset('hf')}
            disabled={exporting !== null}
            className="flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 disabled:opacity-50 transition-all shadow-lg shadow-indigo-200"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            {exporting === 'hf' ? 'Exporting...' : 'Hugging Face'}
          </button>
          <button
            onClick={() => exportDataset('s3')}
            disabled={exporting !== null}
            className="flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 disabled:opacity-50 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
            </svg>
            {exporting === 's3' ? 'Exporting...' : 'Amazon S3'}
          </button>
        </div>
        {exportMessage && (
          <div className="mt-4 p-3 rounded-xl bg-slate-50 text-sm text-slate-600">
            {exportMessage}
          </div>
        )}
      </div>

      {/* Add Prompts Modal */}
      {showAddPromptsModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20">
            <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity" onClick={resetAddPromptsModal} />

            <div className="relative bg-white rounded-3xl shadow-2xl w-full max-w-lg p-6 sm:p-8 overflow-hidden">
              {/* Modal Header */}
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl sm:text-2xl font-bold text-slate-800">Add More Recordings</h2>
                <button
                  onClick={resetAddPromptsModal}
                  className="p-2 rounded-xl hover:bg-slate-100 transition-colors"
                >
                  <svg className="w-5 h-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="space-y-5">
                {/* Input Method */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-3">Input Method</label>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      type="button"
                      onClick={() => setAddPromptsMethod('text')}
                      className={`p-4 rounded-xl border-2 transition-all text-left ${
                        addPromptsMethod === 'text'
                          ? 'border-indigo-500 bg-indigo-50'
                          : 'border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      <svg className={`w-6 h-6 mb-2 ${addPromptsMethod === 'text' ? 'text-indigo-600' : 'text-slate-400'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h7" />
                      </svg>
                      <span className={`font-medium ${addPromptsMethod === 'text' ? 'text-indigo-700' : 'text-slate-600'}`}>Text Input</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setAddPromptsMethod('csv')}
                      className={`p-4 rounded-xl border-2 transition-all text-left ${
                        addPromptsMethod === 'csv'
                          ? 'border-indigo-500 bg-indigo-50'
                          : 'border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      <svg className={`w-6 h-6 mb-2 ${addPromptsMethod === 'csv' ? 'text-indigo-600' : 'text-slate-400'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <span className={`font-medium ${addPromptsMethod === 'csv' ? 'text-indigo-700' : 'text-slate-600'}`}>CSV Upload</span>
                    </button>
                  </div>
                </div>

                {/* Text Input */}
                {addPromptsMethod === 'text' && (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">Prompts (one per line)</label>
                    <textarea
                      value={addPromptsText}
                      onChange={(e) => setAddPromptsText(e.target.value)}
                      className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50/50 text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all resize-none"
                      placeholder="Enter your prompts here, one per line..."
                      rows={6}
                      style={{
                        direction: project?.is_rtl ? 'rtl' : 'ltr',
                        textAlign: project?.is_rtl ? 'right' : 'left'
                      }}
                    />
                    {addPromptsText && (
                      <div className="flex items-center gap-2 mt-2 text-sm text-indigo-600">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                        </svg>
                        {addPromptsText.split('\n').filter(line => line.trim()).length} prompts detected
                      </div>
                    )}
                  </div>
                )}

                {/* CSV Upload */}
                {addPromptsMethod === 'csv' && (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">CSV File with Prompts</label>
                    <div className="relative">
                      <input
                        type="file"
                        accept=".csv"
                        onChange={(e) => e.target.files?.[0] && setAddPromptsFile(e.target.files[0])}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                      />
                      <div className={`p-6 border-2 border-dashed rounded-xl text-center transition-colors ${
                        addPromptsFile ? 'border-green-300 bg-green-50' : 'border-slate-300 hover:border-indigo-300 hover:bg-indigo-50/50'
                      }`}>
                        {addPromptsFile ? (
                          <div className="flex items-center justify-center gap-2 text-green-600">
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                            <span className="font-medium">{addPromptsFile.name}</span>
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
              </div>

              {/* Modal Footer */}
              <div className="flex flex-col-reverse sm:flex-row gap-3 mt-8">
                <button
                  onClick={resetAddPromptsModal}
                  className="flex-1 px-6 py-3 rounded-xl font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={addPrompts}
                  disabled={isAddingPrompts || (addPromptsMethod === 'text' && !addPromptsText.trim()) || (addPromptsMethod === 'csv' && !addPromptsFile)}
                  className="flex-1 px-6 py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-indigo-200"
                >
                  {isAddingPrompts ? 'Adding...' : 'Add Prompts'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Recording;
