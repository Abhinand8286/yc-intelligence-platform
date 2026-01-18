'use client';

import { useState } from 'react';
import Link from 'next/link';

export default function AIPage() {
  const [companyId, setCompanyId] = useState('');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const askAI = async () => {
    if (!companyId || !question) {
      setError('Please enter company ID and a question.');
      return;
    }

    setLoading(true);
    setError('');
    setAnswer('');

    try {
      const res = await fetch(
        `http://127.0.0.1:8000/api/companies/${companyId}/explain`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ question }),
        }
      );

      const data = await res.json();
      setAnswer(data.answer || 'No response.');
    } catch (err) {
      setError('Failed to contact AI service.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8 font-mono">
      {/* Header */}
      <div className="max-w-4xl mx-auto flex justify-between items-center mb-8">
        <h1 className="text-3xl font-extrabold text-purple-600">
          🤖 AI Bot
        </h1>
        <Link
          href="/"
          className="text-sm text-gray-600 hover:text-purple-600 transition"
        >
          ← Back to Dashboard
        </Link>
      </div>

      {/* Card */}
      <div className="max-w-4xl mx-auto bg-white p-6 rounded-xl shadow border border-gray-200">
        {/* Company ID */}
        <div className="mb-4">
          <label className="block text-sm font-semibold text-gray-700 mb-1">
            Company ID
          </label>
          <input
            type="number"
            value={companyId}
            onChange={(e) => setCompanyId(e.target.value)}
            placeholder="e.g. 57"
            className="w-full p-3 rounded-lg border border-gray-300
                       bg-white text-gray-900
                       placeholder-gray-400
                       focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        {/* Question */}
        <div className="mb-4">
          <label className="block text-sm font-semibold text-gray-700 mb-1">
            Ask a question
          </label>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            rows={4}
            placeholder="What does this company do?"
            className="w-full p-3 rounded-lg border border-gray-300
                       bg-white text-gray-900
                       placeholder-gray-400
                       focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        {/* Button */}
        <button
          onClick={askAI}
          disabled={loading}
          className="bg-purple-600 text-white px-5 py-2.5 rounded-lg
                     hover:bg-purple-700 transition
                     disabled:opacity-50"
        >
          {loading ? 'Thinking…' : 'Ask AI'}
        </button>

        {/* Error */}
        {error && (
          <p className="mt-4 text-red-600 text-sm">{error}</p>
        )}

        {/* Answer */}
        {answer && (
          <div className="mt-6 bg-gray-50 p-4 rounded-lg border border-gray-200">
            <h3 className="font-bold mb-2 text-gray-700">AI Answer</h3>
            <p className="text-gray-800 leading-relaxed">{answer}</p>
          </div>
        )}
      </div>
    </div>
  );
}
