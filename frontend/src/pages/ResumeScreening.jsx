import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { screenCandidates } from '../services/api';

const UploadBox = ({ label, multiple, onFiles }) => {
  const inputRef = useRef();
  const [files, setFiles] = useState([]);
  const [drag, setDrag]   = useState(false);

  const handleFiles = (incoming) => {
    const arr = Array.from(incoming);
    const updated = multiple ? [...files, ...arr] : [arr[0]];
    setFiles(updated);
    onFiles(updated);
  };

  const removeFile = (i) => {
    const updated = files.filter((_, idx) => idx !== i);
    setFiles(updated);
    onFiles(updated);
  };

  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-6 flex flex-col gap-4">
      <h3 className="font-bold text-gray-900">{label}</h3>

      <div
        onClick={() => inputRef.current.click()}
        onDragOver={e => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={e => { e.preventDefault(); setDrag(false); handleFiles(e.dataTransfer.files); }}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
          drag ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
        }`}
      >
        <p className="text-4xl mb-2">📁</p>
        <p className="text-sm text-gray-600">
          <span className="text-blue-600 font-medium">Click to upload</span> or drag and drop
        </p>
        <p className="text-xs text-gray-400 mt-1">PDF files only</p>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          multiple={multiple}
          className="hidden"
          onChange={e => handleFiles(e.target.files)}
        />
      </div>

      {files.length > 0 && (
        <div className="space-y-2 max-h-40 overflow-y-auto">
          {files.map((f, i) => (
            <div key={i} className="flex items-center justify-between bg-gray-50 rounded-lg px-4 py-2">
              <div className="flex items-center gap-2 min-w-0">
                <span className="text-red-500">📄</span>
                <span className="text-sm text-gray-700 truncate">{f.name}</span>
              </div>
              <button
                onClick={() => removeFile(i)}
                className="text-gray-400 hover:text-red-500 ml-2 flex-shrink-0"
              >✕</button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default function ResumeScreening() {
  const [jdFile, setJdFile]         = useState(null);
  const [resumes, setResumes]       = useState([]);
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState('');
  const navigate = useNavigate();

  const handleScreen = async () => {
    setError('');
    if (!jdFile)           { setError('Please upload a Job Description PDF.'); return; }
    if (!resumes.length)   { setError('Please upload at least one resume.'); return; }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('jd_file', jdFile);
      resumes.forEach(f => formData.append('files', f));
      await screenCandidates(formData);
      navigate('/results');
    } catch (err) {
      setError('Something went wrong. Make sure backend is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">

      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl p-6 text-white">
        <h2 className="text-xl font-bold mb-1">🤖 AI Resume Screening</h2>
        <p className="text-xs text-gray-400 mt-1">PDF, Word (.docx), or Text files</p>
      </div>

      {/* Upload boxes */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <UploadBox
          label="1. Job Description"
          multiple={false}
          accept=".pdf,.docx,.txt"
          onFiles={files => setJdFile(files[0] || null)}
/>
        <UploadBox
          label="2. Candidate Resumes"
          multiple={true}
          accept=".pdf,.docx,.txt"
          onFiles={files => setResumes(files)}
        />
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-600 rounded-xl px-5 py-3 text-sm">
          {error}
        </div>
      )}

      {/* Screen button */}
      <div className="flex justify-center">
        <button
          onClick={handleScreen}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold px-12 py-4 rounded-xl text-lg transition-colors flex items-center gap-3"
        >
          {loading ? (
            <>
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Processing... (10–20 seconds)
            </>
          ) : (
            <> 🤖 Screen Candidates </>
          )}
        </button>
      </div>

    </div>
  );
}