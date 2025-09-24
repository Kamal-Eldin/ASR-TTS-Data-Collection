import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { encodeWAV, mergeBuffers, createAudioContext } from '../utils/wavEncoder';


const BACKEND_URL = 'http://localhost:8500';

type RecordingMap = { [text: string]: string };

interface Project {
  id: number;
  name: string;
  is_rtl?: boolean;
  created_at: string;
  total_prompts: number;
  recorded_count: number;
  last_recorded_index: number;
}

function Recording() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [prompts, setPrompts] = useState<string[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [recordings, setRecordings] = useState<RecordingMap>({});
  const [existingRecordings, setExistingRecordings] = useState<{[text: string]: {filename: string, recorded_at: string}}>({});
  const [showRecordingsList, setShowRecordingsList] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const audioBuffers = useRef<Float32Array[]>([]);
  const isRecordingRef = useRef<boolean>(false);
  const [exporting, setExporting] = useState<null | 's3' | 'hf'>(null);
  const [exportProgress, setExportProgress] = useState(0);
  const [exportLog, setExportLog] = useState<string[]>([]);
  const [exportError, setExportError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  useEffect(() => {
    if (projectId) {
      loadProject(parseInt(projectId));
    }
    
    // Cleanup audio context on unmount
    return () => {
      if (audioContextRef.current) {
        audioContextRef.current.close();
        audioContextRef.current = null;
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }
    };
  }, [projectId]);

  const loadProject = async (projectId: number) => {
    try {
      const res = await fetch(`${BACKEND_URL}/projects/${projectId}`);
      if (!res.ok) {
        navigate('/');
        return;
      }
      const data = await res.json();
      setProject(data);
      setPrompts(data.prompts);
      
      // Start from the next unrecorded prompt, or from the beginning if all are recorded
      // If last_recorded_index is -1, start from 0. Otherwise, start from the next prompt after the last recorded one
      const startIndex = data.last_recorded_index >= 0 ? data.last_recorded_index + 1 : 0;
      setCurrentIdx(startIndex);
      setRecordings({});
      
      // Load existing recordings
      await loadExistingRecordings(projectId);
      
      console.log('Project loaded:', {
        name: data.name,
        total_prompts: data.total_prompts,
        recorded_count: data.recorded_count,
        last_recorded_index: data.last_recorded_index,
        startIndex: startIndex
      });
    } catch (error) {
      console.error('Failed to load project:', error);
      navigate('/');
    }
  };

  const loadExistingRecordings = async (projectId: number) => {
    try {
      const res = await fetch(`${BACKEND_URL}/projects/${projectId}/recordings`);
      if (res.ok) {
        const data = await res.json();
        const recordingsMap: {[text: string]: {filename: string, recorded_at: string}} = {};
        data.recordings.forEach((rec: any) => {
          recordingsMap[rec.text] = {
            filename: rec.filename,
            recorded_at: rec.recorded_at
          };
        });
        setExistingRecordings(recordingsMap);
        console.log('Existing recordings loaded:', recordingsMap);
      }
    } catch (error) {
      console.error('Failed to load existing recordings:', error);
    }
  };

  // Keyboard shortcuts
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
  }, [isRecording, currentIdx, audioUrl]);

  const refreshProjectData = async () => {
    if (!project) return;
    
    try {
      const res = await fetch(`${BACKEND_URL}/projects/${project.id}`);
      if (res.ok) {
        const data = await res.json();
        setProject(data);
      }
      // Also reload existing recordings
      await loadExistingRecordings(project.id);
    } catch (error) {
      console.error('Failed to refresh project data:', error);
    }
  };

  // Recording logic with raw PCM capture
  const startRecording = async () => {
    if (!navigator.mediaDevices || !project) return alert('No media devices or no project selected');
    
    try {
      // Request high-quality audio with specific constraints
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          channelCount: 1, // Mono recording
          sampleRate: 48000, // High sample rate for quality
          sampleSize: 16, // 16-bit samples
          echoCancellation: false, // Disable processing for raw audio
          noiseSuppression: false,
          autoGainControl: false
        } 
      });
      
      streamRef.current = stream;
      
      // Create audio context for processing
      if (!audioContextRef.current) {
        audioContextRef.current = createAudioContext();
      }
      
      const audioContext = audioContextRef.current;
      const source = audioContext.createMediaStreamSource(stream);
      sourceRef.current = source;
      
      // Create script processor for capturing raw PCM data
      // Buffer size of 4096 for good balance between latency and performance
      const bufferSize = 4096;
      const processor = audioContext.createScriptProcessor(bufferSize, 1, 1);
      processorRef.current = processor;
      
      // Clear previous buffers
      audioBuffers.current = [];
      
      // Capture raw PCM data
      processor.onaudioprocess = (e) => {
        // Use ref to check recording state to avoid closure issues
        if (!isRecordingRef.current) return;
        
        const inputData = e.inputBuffer.getChannelData(0);
        // Create a copy of the data
        const buffer = new Float32Array(inputData.length);
        buffer.set(inputData);
        audioBuffers.current.push(buffer);
        
        // Debug: log buffer info periodically
        if (audioBuffers.current.length % 10 === 0) {
          console.log(`Captured ${audioBuffers.current.length} buffers, latest size: ${buffer.length}`);
        }
      };
      
      // Connect the audio graph
      source.connect(processor);
      processor.connect(audioContext.destination);
      
      // Set both state and ref
      isRecordingRef.current = true;
      setIsRecording(true);
      
      console.log('Recording started, sample rate:', audioContext.sampleRate);
    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Failed to access microphone. Please check permissions.');
    }
  };

  const stopRecording = async () => {
    if (!isRecording || !audioContextRef.current) return;
    
    // Set recording flag to false immediately
    isRecordingRef.current = false;
    setIsRecording(false);
    
    console.log(`Stopping recording. Captured ${audioBuffers.current.length} buffers`);
    
    // Prevent multiple uploads
    if (isUploading) return;
    setIsUploading(true);
    
    try {
      // Disconnect audio nodes
      if (sourceRef.current && processorRef.current) {
        sourceRef.current.disconnect();
        processorRef.current.disconnect();
      }
      
      // Stop all tracks in the stream
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      
      // Merge all audio buffers
      const mergedBuffer = mergeBuffers(audioBuffers.current);
      
      // Get the actual sample rate from the audio context
      const sampleRate = audioContextRef.current.sampleRate;
      
      // Encode to WAV format
      const wavBlob = encodeWAV(mergedBuffer, sampleRate);
      
      // Create object URL for playback
      const url = URL.createObjectURL(wavBlob);
      setAudioUrl(url);
      
      // Upload to backend
      const formData = new FormData();
      formData.append('text', prompts[currentIdx]);
      formData.append('audio', new File([wavBlob], 'recording.wav', { type: 'audio/wav' }));
      formData.append('project_id', project!.id.toString());
      
      const response = await fetch(`${BACKEND_URL}/upload_audio/`, {
        method: 'POST',
        body: formData,
      });
      
      if (response.ok) {
        setRecordings((prev) => ({ ...prev, [prompts[currentIdx]]: url }));
        console.log('Recording uploaded successfully');
      } else {
        console.error('Failed to upload recording');
      }
    } catch (error) {
      console.error('Error stopping recording:', error);
    } finally {
      setIsUploading(false);
      
      // Clear buffers for next recording
      audioBuffers.current = [];
    }
  };

  const playOrStop = () => {
    if (!audioUrl) return;
    if (audioRef.current?.paused) audioRef.current?.play();
    else audioRef.current?.pause();
  };

  const nextPrompt = () => {
    setCurrentIdx((idx) => (idx + 1 < prompts.length ? idx + 1 : idx));
    setAudioUrl(null);
  };

  const prevPrompt = () => {
    setCurrentIdx((idx) => (idx - 1 >= 0 ? idx - 1 : idx));
    setAudioUrl(null);
  };

  const deleteRecording = async () => {
    if (!project) return;
    
    const formData = new FormData();
    formData.append('text', prompts[currentIdx]);
    formData.append('project_id', project.id.toString());
    
    await fetch(`${BACKEND_URL}/delete_audio/`, {
      method: 'POST',
      body: formData,
    });
    setRecordings((prev) => {
      const copy = { ...prev };
      delete copy[prompts[currentIdx]];
      return copy;
    });
    setExistingRecordings((prev) => {
      const copy = { ...prev };
      delete copy[prompts[currentIdx]];
      return copy;
    });
    setAudioUrl(null);
    // Refresh project data to update progress
    await refreshProjectData();
  };

  useEffect(() => {
    // Load audio if exists (either in current session or from existing recordings)
    if (recordings[prompts[currentIdx]]) {
      setAudioUrl(recordings[prompts[currentIdx]]);
    } else if (existingRecordings[prompts[currentIdx]]) {
      // Create audio URL from existing recording
      // const storagePath = 'recordings'; // This should come from settings
      const audioUrl = `${BACKEND_URL}/recordings/${existingRecordings[prompts[currentIdx]].filename}`;
      setAudioUrl(audioUrl);
    } else {
      setAudioUrl(null);
    }
  }, [currentIdx, recordings, existingRecordings, prompts]);

  const exportWithProgress = async (type: 's3' | 'hf') => {
    if (!project) return alert('No project selected');
    setExporting(type);
    setExportProgress(0);
    setExportLog([]);
    setExportError(null);
    
    if (type === 'hf') {
      try {
        setExportLog(log => [...log, 'Starting Hugging Face export...']);
        setExportProgress(10);
        
        const formData = new FormData();
        formData.append('project_id', project.id.toString());
        
        // Set a timeout for the request
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minutes timeout
        
        const res = await fetch(`${BACKEND_URL}/export_hf/`, {
          method: 'POST',
          body: formData,
          signal: controller.signal,
        });
        
        clearTimeout(timeoutId);
        
        if (res.ok) {
          const data = await res.json();
          if (data.status === 'ok') {
            setExportProgress(100);
            setExportLog(log => [...log, `Successfully exported to Hugging Face: ${data.dataset_name}`]);
            setExportLog(log => [...log, `Dataset URL: https://huggingface.co/datasets/${data.dataset_name}`]);
          } else {
            setExportLog(log => [...log, `Error: ${data.detail}`]);
            setExportError(data.detail);
          }
        } else {
          const errorData = await res.json();
          setExportLog(log => [...log, `HTTP Error: ${errorData.detail || 'Unknown error'}`]);
          setExportError(errorData.detail || 'Unknown error');
        }
      } catch (e: any) {
        if (e.name === 'AbortError') {
          setExportLog(log => [...log, 'Export timed out after 5 minutes']);
          setExportError('Export timed out. Please check your internet connection and try again.');
        } else {
          setExportLog(log => [...log, `Error: ${e.message}`]);
          setExportError(e.message);
        }
      }
    }
    
    // Keep modal open for a few seconds to show results
    setTimeout(() => {
      setExporting(null);
    }, 3000);
  };

  if (!project) {
    return (
      <div className="max-w-4xl mx-auto px-6">
        <div className="bg-white rounded-3xl shadow-2xl p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500 mx-auto"></div>
          <p className="mt-4 text-slate-600">Loading project...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{project.name}</h1>
            <p className="text-gray-500 mt-1">Voice Recording Session</p>
          </div>
          <button 
            onClick={() => navigate('/')} 
            className="bg-gray-100 text-gray-600 rounded-lg px-4 py-2 font-semibold hover:bg-gray-200 transition"
          >
            ← Back to Projects
          </button>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">Progress</span>
            <span className="text-sm text-gray-500">
              {project.recorded_count} of {project.total_prompts} recorded
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div 
              className="bg-gray-900 h-3 rounded-full transition-all duration-300" 
              style={{ width: `${(project.recorded_count / project.total_prompts) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Recording Interface */}
        {prompts.length > 0 && (
          <div className="text-center">
            <h2 className="font-bold text-2xl text-gray-900 mb-6">Prompt {currentIdx + 1} of {prompts.length}</h2>
            <div 
              className="text-xl my-6 text-gray-700 bg-gray-100 rounded-lg py-6 px-4 min-h-[60px] leading-relaxed"
              style={{ 
                direction: project?.is_rtl ? 'rtl' : 'ltr',
                textAlign: project?.is_rtl ? 'right' : 'left'
              }}
            >
              {prompts[currentIdx]}
            </div>
            
            <div className="flex justify-center gap-4 my-8">
              <button 
                onClick={prevPrompt}
                disabled={currentIdx === 0}
                className="bg-gray-100 text-gray-700 rounded-lg px-6 py-4 font-bold text-lg shadow hover:bg-gray-200 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                ⏮️ Previous (Right Arrow)
              </button>
              <button 
                onClick={isRecording ? stopRecording : startRecording} 
                disabled={isUploading}
                className={`rounded-lg px-8 py-4 font-bold text-lg shadow transition transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed ${
                  isRecording 
                    ? 'bg-red-600 text-white' 
                    : isUploading
                    ? 'bg-yellow-600 text-white'
                    : 'bg-gray-900 text-white'
                }`}
              >
                {isRecording 
                  ? '⏹️ Stop Recording (Enter)' 
                  : isUploading 
                  ? '⏳ Uploading...' 
                  : '🎤 Start Recording (Enter)'
                }
              </button>
              <button 
                onClick={nextPrompt}
                disabled={currentIdx === prompts.length - 1}
                className="bg-gray-100 text-gray-700 rounded-lg px-6 py-4 font-bold text-lg shadow hover:bg-gray-200 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                ⏭️ Next (Left Arrow)
              </button>
            </div>

            {/* Audio Playback */}
            {audioUrl && (
              <div className="mt-8 p-6 bg-gray-50 rounded-lg">
                <h3 className="font-semibold text-gray-700 mb-4">Recorded Audio</h3>
                <div className="flex items-center justify-center gap-4">
                  <audio ref={audioRef} src={audioUrl} controls className="rounded bg-white shadow" />
                  <button 
                    onClick={playOrStop} 
                    className="bg-gray-100 text-gray-700 rounded-lg px-4 py-2 font-semibold hover:bg-gray-200 transition"
                  >
                    ▶️ Play/Stop (Space)
                  </button>
                  <button 
                    onClick={deleteRecording} 
                    className="bg-red-50 text-red-600 rounded-lg px-4 py-2 font-semibold hover:bg-red-100 transition"
                  >
                    🗑️ Delete
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Export Section */}
        <div className="mt-12 pt-8 border-t border-gray-200">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-bold text-xl text-gray-900">Export Dataset</h3>
            <button 
              onClick={() => setShowRecordingsList(!showRecordingsList)}
              className="bg-gray-100 text-gray-600 rounded-lg px-4 py-2 font-semibold hover:bg-gray-200 transition"
            >
              {showRecordingsList ? 'Hide' : 'Show'} All Recordings
            </button>
          </div>
          
          {/* Recordings List */}
          {showRecordingsList && (
            <div className="mb-6 p-6 bg-gray-50 rounded-lg">
              <h4 className="font-semibold text-gray-700 mb-4">All Recordings ({Object.keys(existingRecordings).length})</h4>
              {Object.keys(existingRecordings).length > 0 ? (
                <div className="space-y-3 max-h-60 overflow-y-auto">
                  {prompts.map((prompt, index) => {
                    const recording = existingRecordings[prompt];
                    return (
                      <div key={index} className="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-200">
                        <div className="flex-1">
                          <div className="font-medium text-gray-900">Prompt {index + 1}</div>
                          <div 
                            className="text-sm text-gray-600 truncate max-w-md"
                            style={{ 
                              direction: project?.is_rtl ? 'rtl' : 'ltr',
                              textAlign: project?.is_rtl ? 'right' : 'left'
                            }}
                          >
                            {prompt}
                          </div>
                          {recording && (
                            <div className="text-xs text-gray-500 mt-1">
                              Recorded: {new Date(recording.recorded_at).toLocaleString()}
                            </div>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          {recording ? (
                            <>
                              <audio 
                                controls 
                                className="h-8 rounded bg-gray-100"
                                src={`${BACKEND_URL}/recordings/${recording.filename}`}
                              />
                              <button 
                                onClick={() => {
                                  setCurrentIdx(index);
                                  setAudioUrl(`${BACKEND_URL}/recordings/${recording.filename}`);
                                }}
                                className="bg-gray-100 text-gray-700 rounded px-3 py-1 text-sm font-medium hover:bg-gray-200 transition"
                              >
                                Go to
                              </button>
                            </>
                          ) : (
                            <span className="text-gray-400 text-sm">Not recorded</span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-4">No recordings yet</p>
              )}
            </div>
          )}
          
          <div className="flex justify-center gap-4">
            <button 
              onClick={() => exportWithProgress('s3')} 
              className="bg-gray-900 text-white rounded-lg px-6 py-3 font-semibold shadow hover:bg-gray-800 transition"
            >
              📤 Export to S3
            </button>
            <button 
              onClick={() => exportWithProgress('hf')} 
              className="bg-gray-900 text-white rounded-lg px-6 py-3 font-semibold shadow hover:bg-gray-800 transition"
            >
              🤗 Export to Hugging Face
            </button>
          </div>
        </div>

        {/* Keyboard Shortcuts */}
        <div className="mt-8 text-gray-500 text-sm text-center">
          <p className="mb-2 font-semibold">Keyboard Shortcuts:</p>
          <ul className="list-none p-0 m-0 space-y-1">
            <li>⏎ <b>Enter</b>: Start/Stop Recording</li>
            <li>← <b>Left Arrow</b>: Next Prompt</li>
            <li>→ <b>Right Arrow</b>: Previous Prompt</li>
            <li>␣ <b>Space</b>: Play/Stop Audio</li>
          </ul>
        </div>

        {/* Export Progress Modal */}
        {exporting && (
          <div className="fixed top-0 left-0 w-screen h-screen bg-black/60 z-50 flex items-center justify-center">
            <div className="bg-white p-8 rounded-lg min-w-[400px] shadow-lg">
              <h2 className="font-bold text-xl text-gray-900 mb-4">
                Exporting to {exporting === 's3' ? 'Amazon S3' : 'Hugging Face'}
              </h2>
              <div className="my-4">
                <div className="bg-gray-200 h-6 rounded-full overflow-hidden">
                  <div 
                    className="bg-gray-900 h-full transition-all" 
                    style={{ width: `${exportProgress}%` }} 
                  />
                </div>
                <div className="mt-2 text-gray-700 font-semibold">{exportProgress}%</div>
              </div>
              <div className="max-h-40 overflow-y-auto bg-gray-50 p-3 rounded text-sm text-gray-700">
                {exportLog.map((line, i) => <div key={i}>{line}</div>)}
                {exportError && <div className="text-red-600">{exportError}</div>}
              </div>
              <button 
                onClick={() => setExporting(null)} 
                className="mt-4 bg-gray-100 text-gray-700 rounded-lg px-4 py-2 font-semibold hover:bg-gray-200 transition"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Recording; 