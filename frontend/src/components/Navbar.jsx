import React from 'react';
import { useLocation } from 'react-router-dom';

const pageTitles = {
  '/':          { title: 'Dashboard',         subtitle: 'Welcome back!' },
  '/screening': { title: 'Resume Screening',  subtitle: 'Upload JD and resumes to start AI matching' },
  '/results':   { title: 'Screening Results', subtitle: 'Ranked candidates based on job match' },
  '/analytics': { title: 'Analytics',         subtitle: 'Insights from your screening data' },
};

export default function Navbar() {
  const location = useLocation();
  const page     = pageTitles[location.pathname] || pageTitles['/'];
  const user     = JSON.parse(sessionStorage.getItem('user') || '{}');

  return (
    <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">

      {/* Page title */}
      <div>
        <h2 className="text-lg font-bold text-gray-900">{page.title}</h2>
        <p className="text-sm text-gray-500">{page.subtitle}</p>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-4">
        {/* Greeting */}
        <span className="text-sm text-gray-600 hidden sm:block">
          Hello, <span className="font-medium text-gray-900">{user.name?.split(' ')[0] || 'HR'}</span>
        </span>

        {/* Avatar */}
        <div className="w-9 h-9 bg-blue-600 rounded-full flex items-center justify-center">
          <span className="text-white text-sm font-bold">
            {user.name?.charAt(0).toUpperCase() || 'H'}
          </span>
        </div>
      </div>

    </div>
  );
}