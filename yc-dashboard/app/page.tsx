'use client';
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

// HELPER: Safely parse tags without crashing
const parseTags = (tagData: any) => {
  if (!tagData) return '-';
  try {
    // Try to parse as JSON (e.g., ["SaaS", "B2B"])
    const parsed = JSON.parse(tagData);
    if (Array.isArray(parsed)) {
      return parsed.slice(0, 3).join(', ');
    }
    return parsed; // Return as is if valid JSON but not an array
  } catch (e) {
    // If parsing fails (e.g., it's just a plain string), return it directly
    return tagData.toString().replace(/[\[\]"]/g, ''); 
  }
};

export default function Home() {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  
  // Filter States
  const [batchFilter, setBatchFilter] = useState('');
  const [stageFilter, setStageFilter] = useState('');
  const [locationFilter, setLocationFilter] = useState('');

  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [stats, setStats] = useState([]);

  // Load Data Function
  const fetchCompanies = () => {
    setLoading(true);
    const params = new URLSearchParams({
      page: page.toString(),
      limit: '20',
      search: search,
      batch: batchFilter,
      stage: stageFilter,
      location: locationFilter
    });

    fetch(`/api/companies?${params.toString()}`)
      .then((res) => res.json())
      .then((data) => {
        setCompanies(data.data);
        setTotalPages(Math.ceil(data.pagination.total / 20));
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch companies:", err);
        setLoading(false);
      });
  };

  // Fetch when any filter or page changes
  useEffect(() => {
    setPage(1); // Reset to page 1 if filters change
  }, [search, batchFilter, stageFilter, locationFilter]);

  useEffect(() => {
    fetchCompanies();
  }, [page, search, batchFilter, stageFilter, locationFilter]);

  // Load Batch Stats
  useEffect(() => {
    fetch('/api/analytics')
      .then(res => res.json())
      .then(data => {
        if(data.batches) setStats(data.batches);
      })
      .catch(err => console.error("Failed to fetch stats:", err));
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 p-8 pb-20 font-mono text-gray-800">
      
      {/* Header */}
      <div className="max-w-6xl mx-auto flex justify-between items-center mb-8">
        <div>
          <h1 className="text-4xl font-extrabold text-orange-600 tracking-tight">YC Intelligence</h1>
          <p className="text-gray-500 mt-2">Tracking {companies.length > 0 ? '1000+' : '...'} companies</p>
        </div>
        <div className="flex gap-4">
           <Link href="/analytics" className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition">
            📊 Global Analytics
          </Link>
        </div>
      </div>

      {/* Top Chart Section */}
      <div className="max-w-6xl mx-auto mb-10 bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <h2 className="text-lg font-bold mb-4">Top Batches by Volume</h2>
        <div className="h-48 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={stats}>
              <XAxis dataKey="batch" tick={{fontSize: 12}} />
              <Tooltip cursor={{fill: '#f3f4f6'}} />
              <Bar dataKey="count" fill="#f97316" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* FILTER BAR */}
      <div className="max-w-6xl mx-auto mb-6 flex flex-wrap gap-4 bg-white p-4 rounded-lg shadow-sm">
        <input
          type="text"
          placeholder="Search companies..."
          className="p-2 border rounded w-64 focus:outline-none focus:ring-2 focus:ring-orange-500"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />

        <select 
          className="p-2 border rounded focus:outline-none focus:ring-2 focus:ring-orange-500"
          value={batchFilter}
          onChange={(e) => setBatchFilter(e.target.value)}
        >
          <option value="">All Batches</option>
          <option value="W24">Winter 2024</option>
          <option value="S23">Summer 2023</option>
          <option value="W23">Winter 2023</option>
        </select>

        <select 
          className="p-2 border rounded focus:outline-none focus:ring-2 focus:ring-orange-500"
          value={stageFilter}
          onChange={(e) => setStageFilter(e.target.value)}
        >
          <option value="">All Stages</option>
          <option value="Active">Active</option>
          <option value="Public">Public</option>
          <option value="Acquired">Acquired</option>
          <option value="Inactive">Inactive</option>
        </select>

        <select 
          className="p-2 border rounded focus:outline-none focus:ring-2 focus:ring-orange-500"
          value={locationFilter}
          onChange={(e) => setLocationFilter(e.target.value)}
        >
          <option value="">All Locations</option>
          <option value="San Francisco">San Francisco</option>
          <option value="New York">New York</option>
          <option value="London">London</option>
          <option value="Remote">Remote</option>
          <option value="Bangalore">Bangalore</option>
        </select>
      </div>

      {/* Data Table */}
      <div className="max-w-6xl mx-auto bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200 text-xs uppercase text-gray-500 tracking-wider">
                <th className="p-4 font-semibold">Company</th>
                <th className="p-4 font-semibold">Batch</th>
                <th className="p-4 font-semibold">Stage</th>
                <th className="p-4 font-semibold">Tags</th>
                <th className="p-4 font-semibold">Contact</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {loading ? (
                <tr><td colSpan={5} className="p-8 text-center text-gray-500">Loading data...</td></tr>
              ) : companies.map((c: any) => (
                <tr key={c.id} className="hover:bg-orange-50 transition group">
                  <td className="p-4">
                    <Link href={`/companies/${c.id}`} className="font-bold text-gray-900 group-hover:text-orange-600">
                      {c.name}
                    </Link>
                    <div className="text-xs text-gray-400 mt-1">{c.domain ? c.domain.replace('https://', '') : ''}</div>
                  </td>
                  <td className="p-4">
                    <span className="bg-gray-100 text-gray-600 px-2 py-1 rounded text-xs font-medium">
                      {c.batch || 'N/A'}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      c.stage === 'Active' ? 'bg-green-100 text-green-700' :
                      c.stage === 'Public' ? 'bg-purple-100 text-purple-700' :
                      c.stage === 'Acquired' ? 'bg-blue-100 text-blue-700' :
                      'bg-red-100 text-red-700'
                    }`}>
                      {c.stage || 'Unknown'}
                    </span>
                  </td>
                  {/* SAFE TAG RENDERING */}
                  <td className="p-4 max-w-xs truncate text-sm text-gray-500">
                    {parseTags(c.tags)}
                  </td>
                  <td className="p-4 text-sm text-gray-500">
                     {c.contact_email ? (
                       <span className="text-blue-600">✉️ Found</span>
                     ) : (
                       <span className="text-gray-300">-</span>
                     )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination Block */}
      <div className="max-w-6xl mx-auto mt-8 flex justify-between items-center">
        <button 
          disabled={page === 1} 
          onClick={() => setPage(page - 1)}
          className="px-6 py-2 border border-gray-300 rounded-lg bg-white font-medium text-gray-700 disabled:opacity-50 hover:bg-gray-50 transition"
        >
          ← Previous
        </button>
        
        <span className="text-sm font-semibold text-gray-600">
          Page {page} of {totalPages || 1}
        </span>
        
        <button 
          disabled={page >= totalPages} 
          onClick={() => setPage(page + 1)}
          className="px-6 py-2 border border-gray-300 rounded-lg bg-white font-medium text-gray-700 disabled:opacity-50 hover:bg-gray-50 transition"
        >
          Next →
        </button>
      </div>

      {/* NEW FOOTER with ADMIN LINK */}
      <footer className="max-w-6xl mx-auto mt-12 pt-8 border-t border-gray-200 flex justify-between items-center text-sm text-gray-400">
        <p>© 2026 YC Intelligence Platform. All rights reserved.</p>
        <div className="flex gap-4">
          <Link href="/admin" className="hover:text-orange-600 transition flex items-center gap-1">
            🔒 System Status
          </Link>
        </div>
      </footer>

    </div>
  );
}