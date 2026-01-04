'use client';
import { useState, useEffect } from 'react';
import Link from 'next/link';

export default function AdminPage() {
  const [runs, setRuns] = useState([]);

  useEffect(() => {
    fetch('/api/runs')
      .then(res => res.json())
      .then(data => setRuns(data));
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-8 font-mono">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-green-400">System Status / Scraper Logs</h1>
          <Link href="/" className="text-gray-400 hover:text-white">← Back to Dashboard</Link>
        </div>

        <div className="bg-gray-800 rounded-xl overflow-hidden shadow-lg border border-gray-700">
          <table className="w-full text-left">
            <thead className="bg-gray-700 text-gray-300 uppercase text-xs">
              <tr>
                <th className="p-4">Run ID</th>
                <th className="p-4">Date</th>
                <th className="p-4">Status</th>
                <th className="p-4">Found</th>
                <th className="p-4">New / Upd</th>
                <th className="p-4">Avg Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {runs.map((run: any) => (
                <tr key={run.id} className="hover:bg-gray-700/50 transition">
                  <td className="p-4 text-gray-500">#{run.id}</td>
                  <td className="p-4">
                    {new Date(run.started_at).toLocaleString()}
                  </td>
                  <td className="p-4">
                    <span className={`px-2 py-1 rounded text-xs font-bold ${
                      run.status === 'success' ? 'bg-green-900 text-green-300' : 
                      run.status === 'running' ? 'bg-blue-900 text-blue-300' : 
                      'bg-red-900 text-red-300'
                    }`}>
                      {run.status?.toUpperCase()}
                    </span>
                  </td>
                  <td className="p-4 font-bold">{run.companies_found}</td>
                  <td className="p-4 text-sm">
                    <span className="text-green-400">+{run.companies_added}</span> / 
                    <span className="text-blue-400"> {run.companies_updated}</span>
                  </td>
                  <td className="p-4 text-gray-400">
                    {run.avg_time_per_company_ms ? `${Math.round(run.avg_time_per_company_ms)}ms` : '-'}
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