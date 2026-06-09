import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getCandidates } from '../services/api';

const StatCard = ({ label, value, icon, color }) => (
  <div className="bg-white rounded-2xl p-6 border border-gray-200 flex items-center gap-4">
    <div className={`w-14 h-14 rounded-xl flex items-center justify-center text-2xl ${color}`}>
      {icon}
    </div>
    <div>
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-3xl font-bold text-gray-900">{value}</p>
    </div>
  </div>
);

export default function Dashboard() {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading]       = useState(true);
  const user = JSON.parse(sessionStorage.getItem('user') || '{}');

  useEffect(() => {
    getCandidates()
      .then(data => setCandidates(data))
      .catch(() => setCandidates([]))
      .finally(() => setLoading(false));
  }, []);

  const total       = candidates.length;
  const shortlisted = candidates.filter(c => c.status === 'Shortlisted').length;
  const inReview    = candidates.filter(c => c.status === 'In Review').length;
  const rejected    = candidates.filter(c => c.status === 'Rejected').length;
  const avgScore    = total
    ? (candidates.reduce((a, c) => a + c.score, 0) / total).toFixed(1)
    : 0;
  const topCandidate = candidates[0];

  return (
    <div className="space-y-6">

      {/* Welcome banner */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl p-6 text-white">
        <h2 className="text-2xl font-bold mb-1">
          Welcome back, {user.name?.split(' ')[0] || 'HR'} 👋
        </h2>
        <p className="text-blue-100 mb-4">
          {total > 0
            ? `You have ${total} candidates screened. ${shortlisted} shortlisted.`
            : 'No screenings yet. Start by uploading a job description and resumes.'}
        </p>
        <Link
          to="/screening"
          className="inline-block bg-white text-blue-600 font-semibold px-5 py-2 rounded-xl text-sm hover:bg-blue-50 transition-colors"
        >
          + New Screening
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Candidates" value={total}       icon="👥" color="bg-blue-50" />
        <StatCard label="Shortlisted"      value={shortlisted} icon="✅" color="bg-green-50" />
        <StatCard label="In Review"        value={inReview}    icon="🔍" color="bg-yellow-50" />
        <StatCard label="Avg Match Score"  value={`${avgScore}%`} icon="📊" color="bg-purple-50" />
      </div>

      {/* Top candidate + recent results */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Top candidate */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6">
          <h3 className="font-bold text-gray-900 mb-4">🏆 Top Candidate</h3>
          {topCandidate ? (
            <div className="space-y-3">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center">
                  <span className="text-white font-bold">
                    {topCandidate.name?.charAt(0)}
                  </span>
                </div>
                <div>
                  <p className="font-semibold text-gray-900">{topCandidate.name}</p>
                  <p className="text-sm text-gray-500">{topCandidate.email}</p>
                </div>
                <div className="ml-auto text-right">
                  <p className="text-2xl font-bold text-blue-600">{topCandidate.score}%</p>
                  <p className="text-xs text-gray-500">match score</p>
                </div>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{ width: `${topCandidate.score}%` }}
                />
              </div>
              <p className="text-sm text-gray-600">{topCandidate.summary}</p>
              <div className="flex flex-wrap gap-2 mt-2">
                {topCandidate.skills?.slice(0, 5).map(skill => (
                  <span key={skill} className="bg-blue-50 text-blue-700 text-xs px-3 py-1 rounded-full font-medium">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-400">
              <p className="text-4xl mb-2">🤖</p>
              <p>No screenings yet</p>
              <Link to="/screening" className="text-blue-600 text-sm hover:underline">
                Start screening →
              </Link>
            </div>
          )}
        </div>

        {/* Recent candidates */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-gray-900">📋 Recent Candidates</h3>
            <Link to="/results" className="text-blue-600 text-sm hover:underline">View all →</Link>
          </div>
          {candidates.length > 0 ? (
            <div className="space-y-3">
              {candidates.slice(0, 4).map((c, i) => (
                <div key={i} className="flex items-center gap-3 py-2 border-b border-gray-50 last:border-0">
                  <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center text-sm font-bold text-gray-600">
                    #{c.rank}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">{c.name}</p>
                    <p className="text-xs text-gray-500 truncate">{c.education}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold text-gray-900">{c.score}%</p>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      c.status === 'Shortlisted' ? 'bg-green-100 text-green-700' :
                      c.status === 'In Review'   ? 'bg-yellow-100 text-yellow-700' :
                                                   'bg-red-100 text-red-700'
                    }`}>
                      {c.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-400">
              <p className="text-4xl mb-2">📭</p>
              <p>No candidates yet</p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}