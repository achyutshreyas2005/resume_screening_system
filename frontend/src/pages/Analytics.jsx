import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getCandidates } from '../services/api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend
} from 'recharts';

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];

const StatCard = ({ label, value, icon, color }) => (
  <div className="bg-white rounded-2xl border border-gray-200 p-6 flex items-center gap-4">
    <div className={`w-14 h-14 rounded-xl flex items-center justify-center text-2xl ${color}`}>
      {icon}
    </div>
    <div>
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-3xl font-bold text-gray-900">{value}</p>
    </div>
  </div>
);

export default function Analytics() {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading]       = useState(true);

  useEffect(() => {
    getCandidates()
      .then(data => setCandidates(data))
      .catch(() => setCandidates([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-gray-500">Loading analytics...</p>
      </div>
    </div>
  );

  if (candidates.length === 0) return (
    <div className="bg-white rounded-2xl border border-gray-200 p-12 text-center">
      <p className="text-4xl mb-3">📊</p>
      <p className="text-gray-500 mb-4">No data yet. Run a screening first to see analytics.</p>
      <Link
        to="/screening"
        className="bg-blue-600 text-white px-6 py-2 rounded-xl text-sm font-medium hover:bg-blue-700"
      >
        Start Screening →
      </Link>
    </div>
  );

  // ── Compute stats ────────────────────────────────────────────────────────────
  const total       = candidates.length;
  const shortlisted = candidates.filter(c => c.status === 'Shortlisted').length;
  const inReview    = candidates.filter(c => c.status === 'In Review').length;
  const rejected    = candidates.filter(c => c.status === 'Rejected').length;
  const avgScore    = (candidates.reduce((a, c) => a + c.score, 0) / total).toFixed(1);
  const topScore    = Math.max(...candidates.map(c => c.score));

  // Skills frequency
  const skillCount = {};
  candidates.flatMap(c => c.skills).forEach(s => {
    skillCount[s] = (skillCount[s] || 0) + 1;
  });
  const topSkills = Object.entries(skillCount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([skill, count]) => ({ skill, count }));

  // Status breakdown for pie chart
  const pieData = [
    { name: 'Shortlisted', value: shortlisted },
    { name: 'In Review',   value: inReview },
    { name: 'Rejected',    value: rejected },
  ].filter(d => d.value > 0);

  // Score distribution for bar chart
  const scoreData = candidates.map(c => ({
    name:  c.name.split(' ')[0],
    score: c.score,
  }));

  return (
    <div className="space-y-6">

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard label="Total Screened"  value={total}         icon="👥" color="bg-blue-50" />
        <StatCard label="Average Score"   value={`${avgScore}%`} icon="📊" color="bg-purple-50" />
        <StatCard label="Highest Score"   value={`${topScore}%`} icon="🏆" color="bg-yellow-50" />
        <StatCard label="Shortlisted"     value={shortlisted}   icon="✅" color="bg-green-50" />
        <StatCard label="In Review"       value={inReview}      icon="🔍" color="bg-orange-50" />
        <StatCard label="Rejected"        value={rejected}      icon="❌" color="bg-red-50" />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Score bar chart */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6">
          <h3 className="font-bold text-gray-900 mb-4">📈 Candidate Scores</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={scoreData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
              <Tooltip
                formatter={(val) => [`${val}%`, 'Score']}
                contentStyle={{ borderRadius: '12px', border: '1px solid #E5E7EB' }}
              />
              <Bar dataKey="score" fill="#3B82F6" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Status pie chart */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6">
          <h3 className="font-bold text-gray-900 mb-4">🎯 Status Breakdown</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                outerRadius={90}
                dataKey="value"
                label={({ name, value }) => `${name}: ${value}`}
                labelLine={false}
              >
                {pieData.map((_, i) => (
                  <Cell key={i} fill={['#10B981', '#F59E0B', '#EF4444'][i]} />
                ))}
              </Pie>
              <Legend />
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

      </div>

      {/* Top skills */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6">
        <h3 className="font-bold text-gray-900 mb-4">🛠 Top Skills Across Candidates</h3>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={topSkills} layout="vertical" margin={{ left: 20, right: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
            <XAxis type="number" tick={{ fontSize: 12 }} />
            <YAxis dataKey="skill" type="category" tick={{ fontSize: 12 }} width={80} />
            <Tooltip
              formatter={(val) => [val, 'Candidates']}
              contentStyle={{ borderRadius: '12px', border: '1px solid #E5E7EB' }}
            />
            <Bar dataKey="count" radius={[0, 6, 6, 0]}>
              {topSkills.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Candidate ranking table */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6">
        <h3 className="font-bold text-gray-900 mb-4">📋 Full Ranking</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="text-left py-3 px-4 text-gray-500 font-medium">Rank</th>
                <th className="text-left py-3 px-4 text-gray-500 font-medium">Name</th>
                <th className="text-left py-3 px-4 text-gray-500 font-medium">Score</th>
                <th className="text-left py-3 px-4 text-gray-500 font-medium">Status</th>
                <th className="text-left py-3 px-4 text-gray-500 font-medium">Skills</th>
              </tr>
            </thead>
            <tbody>
              {candidates.map((c, i) => (
                <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="py-3 px-4 font-bold text-blue-600">#{c.rank}</td>
                  <td className="py-3 px-4">
                    <p className="font-medium text-gray-900">{c.name}</p>
                    <p className="text-xs text-gray-500">{c.email}</p>
                  </td>
                  <td className="py-3 px-4">
                    <p className="font-bold text-gray-900">{c.score}%</p>
                    <div className="w-20 bg-gray-100 rounded-full h-1.5 mt-1">
                      <div
                        className={`h-1.5 rounded-full ${
                          c.score >= 60 ? 'bg-green-500' :
                          c.score >= 40 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${c.score}%` }}
                      />
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`text-xs px-3 py-1 rounded-full font-medium ${
                      c.status === 'Shortlisted' ? 'bg-green-100 text-green-700' :
                      c.status === 'In Review'   ? 'bg-yellow-100 text-yellow-700' :
                                                   'bg-red-100 text-red-700'
                    }`}>
                      {c.status}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex flex-wrap gap-1">
                      {c.skills?.slice(0, 3).map(s => (
                        <span key={s} className="bg-blue-50 text-blue-700 text-xs px-2 py-0.5 rounded-full">
                          {s}
                        </span>
                      ))}
                      {c.skills?.length > 3 && (
                        <span className="text-xs text-gray-400">+{c.skills.length - 3}</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}