import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getCandidates } from '../services/api';

const StatusBadge = ({ status }) => {
  const colors = {
    'Shortlisted': 'bg-green-100 text-green-700',
    'In Review':   'bg-yellow-100 text-yellow-700',
    'Rejected':    'bg-red-100 text-red-700',
  };
  return (
    <span className={`text-xs px-3 py-1 rounded-full font-medium ${colors[status] || 'bg-gray-100 text-gray-600'}`}>
      {status}
    </span>
  );
};

const ScoreBar = ({ score }) => {
  const color = score >= 60 ? 'bg-green-500' : score >= 40 ? 'bg-yellow-500' : 'bg-red-500';
  return (
    <div className="w-full bg-gray-100 rounded-full h-2 mt-1">
      <div className={`${color} h-2 rounded-full transition-all`} style={{ width: `${score}%` }} />
    </div>
  );
};

export default function Results() {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading]       = useState(true);
  const [filter, setFilter]         = useState('all');
  const [expanded, setExpanded]     = useState(null);

  useEffect(() => {
    getCandidates()
      .then(data => setCandidates(data))
      .catch(() => setCandidates([]))
      .finally(() => setLoading(false));
  }, []);

  const filtered = candidates.filter(c => {
    if (filter === 'shortlisted') return c.status === 'Shortlisted';
    if (filter === 'review')      return c.status === 'In Review';
    if (filter === 'rejected')    return c.status === 'Rejected';
    return true;
  });

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-gray-500">Loading results...</p>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900">
            Found {filtered.length} candidate{filtered.length !== 1 ? 's' : ''}
          </h2>
          <p className="text-sm text-gray-500">Ranked by AI match score</p>
        </div>

        {/* Filter */}
        <div className="flex gap-2 flex-wrap">
          {['all', 'shortlisted', 'review', 'rejected'].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors capitalize ${
                filter === f
                  ? 'bg-blue-600 text-white'
                  : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}
            >
              {f === 'all' ? 'All' : f === 'review' ? 'In Review' : f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Empty state */}
      {filtered.length === 0 && (
        <div className="bg-white rounded-2xl border border-gray-200 p-12 text-center">
          <p className="text-4xl mb-3">📭</p>
          <p className="text-gray-500 mb-4">
            {candidates.length === 0
              ? 'No screenings yet. Upload a JD and resumes to get started.'
              : 'No candidates match the selected filter.'}
          </p>
          {candidates.length === 0 && (
            <Link
              to="/screening"
              className="bg-blue-600 text-white px-6 py-2 rounded-xl text-sm font-medium hover:bg-blue-700"
            >
              Start Screening →
            </Link>
          )}
        </div>
      )}

      {/* Candidate cards */}
      <div className="space-y-4">
        {filtered.map((c, i) => (
          <div
            key={i}
            className="bg-white rounded-2xl border border-gray-200 p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex flex-col sm:flex-row sm:items-center gap-4">

              {/* Rank */}
              <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center flex-shrink-0">
                <span className="text-blue-600 font-bold text-lg">#{c.rank}</span>
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 flex-wrap">
                  <h3 className="font-bold text-gray-900">{c.name}</h3>
                  <StatusBadge status={c.status} />
                </div>
                <p className="text-sm text-gray-500 mt-0.5">{c.email} · {c.phone}</p>
                <p className="text-sm text-gray-600 mt-1 truncate">{c.education}</p>
              </div>

              {/* Score */}
              <div className="text-right flex-shrink-0 w-28">
                <p className="text-3xl font-bold text-blue-600">{c.score}%</p>
                <ScoreBar score={c.score} />
                <p className="text-xs text-gray-400 mt-1">match score</p>
              </div>
            </div>

            {/* Skills */}
            <div className="flex flex-wrap gap-2 mt-4">
              {c.skills?.slice(0, 8).map(skill => (
                <span key={skill} className="bg-blue-50 text-blue-700 text-xs px-3 py-1 rounded-full font-medium">
                  {skill}
                </span>
              ))}
              {c.missingSkills?.length > 0 && c.missingSkills.slice(0, 3).map(skill => (
                <span key={skill} className="bg-red-50 text-red-500 text-xs px-3 py-1 rounded-full font-medium">
                  ✕ {skill}
                </span>
              ))}
            </div>

            {/* Expand */}
            <button
              onClick={() => setExpanded(expanded === i ? null : i)}
              className="mt-4 text-sm text-blue-600 hover:underline"
            >
              {expanded === i ? '▲ Hide details' : '▼ Show details'}
            </button>

            {/* Expanded details */}
            {expanded === i && (
              <div className="mt-4 pt-4 border-t border-gray-100 grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="font-medium text-gray-700 mb-1">🎓 Education</p>
                  <p className="text-gray-600">{c.education}</p>
                </div>
                <div>
                  <p className="font-medium text-gray-700 mb-1">💼 Experience</p>
                  <p className="text-gray-600">{c.experience}</p>
                </div>
                <div className="sm:col-span-2">
                  <p className="font-medium text-gray-700 mb-1">🚀 Projects</p>
                  <p className="text-gray-600">{c.projects || 'Not specified'}</p>
                </div>
                <div className="sm:col-span-2">
                  <p className="font-medium text-gray-700 mb-1">🤖 AI Summary</p>
                  <p className="text-gray-600">{c.summary}</p>
                </div>
              </div>
            )}

          </div>
        ))}
      </div>

    </div>
  );
}