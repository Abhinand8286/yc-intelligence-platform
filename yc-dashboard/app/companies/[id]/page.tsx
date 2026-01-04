'use client';
import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';

export default function CompanyDetail() {
  const { id } = useParams();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/companies/${id}`)
      .then((res) => res.json())
      .then((data) => {
        setData(data);
        setLoading(false);
      });
  }, [id]);

  if (loading) return <div className="p-10 font-mono">Loading Company History...</div>;
  if (!data || !data.company) return <div className="p-10 font-mono">Company Not Found</div>;

  const { company, history } = data;
  const latest = history[0] || {}; // The most recent snapshot

  return (
    <div className="min-h-screen bg-gray-50 p-8 font-mono text-gray-800">
      
      {/* Header / Nav */}
      <div className="max-w-4xl mx-auto mb-6">
        <Link href="/" className="text-blue-600 hover:underline">← Back to Dashboard</Link>
      </div>

      {/* 1. Main Company Card */}
      <div className="max-w-4xl mx-auto bg-white rounded-xl shadow-sm border border-gray-200 p-8 mb-8">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-4xl font-extrabold text-orange-600 mb-2">{company.name}</h1>
            <a href={company.domain} target="_blank" className="text-blue-500 hover:underline text-sm">
              {company.domain} ↗
            </a>
          </div>
          <div className={`px-3 py-1 rounded text-sm font-bold ${
             latest.stage === 'Active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
          }`}>
            {latest.stage || 'Unknown Stage'}
          </div>
        </div>

        <p className="mt-6 text-lg text-gray-700 leading-relaxed">
          {latest.description || "No description available."}
        </p>

        <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="bg-gray-50 p-3 rounded">
            <span className="block text-gray-400 text-xs uppercase">Batch</span>
            <span className="font-bold">{latest.batch || 'N/A'}</span>
          </div>
          <div className="bg-gray-50 p-3 rounded">
            <span className="block text-gray-400 text-xs uppercase">Location</span>
            <span className="font-bold">{latest.location || 'N/A'}</span>
          </div>
          <div className="bg-gray-50 p-3 rounded">
             <span className="block text-gray-400 text-xs uppercase">Web Check</span>
             {company.has_careers_page ? <span className="text-green-600">✅ Careers</span> : <span>-</span>}
          </div>
           <div className="bg-gray-50 p-3 rounded">
             <span className="block text-gray-400 text-xs uppercase">Contact</span>
             {company.contact_email ? <span className="text-blue-600">{company.contact_email}</span> : <span>-</span>}
          </div>
        </div>
      </div>

      {/* 2. The Timeline (History) */}
      <div className="max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold mb-4">Evolution Timeline</h2>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-gray-50 border-b border-gray-200 text-xs uppercase text-gray-500">
              <tr>
                <th className="p-4">Date Scraped</th>
                <th className="p-4">Stage</th>
                <th className="p-4">Employees</th>
                <th className="p-4">Description Change?</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {history.map((snap: any, i: number) => (
                <tr key={snap.id} className="hover:bg-gray-50">
                  <td className="p-4 text-gray-600">
                    {new Date(snap.scraped_at).toLocaleDateString()} 
                    <span className="text-xs text-gray-400 ml-2">
                      {new Date(snap.scraped_at).toLocaleTimeString()}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className="font-medium text-gray-800">{snap.stage}</span>
                  </td>
                  <td className="p-4 text-gray-500">
                    {snap.employee_range || '-'}
                  </td>
                  <td className="p-4 text-sm text-gray-500 truncate max-w-xs">
                    {snap.description ? snap.description.substring(0, 50) + '...' : '-'}
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