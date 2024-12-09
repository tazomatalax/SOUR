import React from 'react';
import Layout from './components/Layout';
import MetricsPanel from './components/MetricsPanel';
import MetricsChart from './components/charts/MetricsChart';
import FeedEventsList from './components/FeedEventsList';
import { useWebSocket } from './hooks/useWebSocket';

function App() {
  useWebSocket();

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h2>
          <div className="flex space-x-4">
            <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              Start Feed
            </button>
            <button className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600">
              Export Data
            </button>
          </div>
        </div>

        <MetricsPanel />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Real-time Metrics</h3>
            <MetricsChart />
          </div>

          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Feed Events</h3>
            <FeedEventsList />
          </div>
        </div>
      </div>
    </Layout>
  );
}

export default App;