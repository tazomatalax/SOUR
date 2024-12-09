import React from 'react';
import { format } from 'date-fns';
import { Beaker } from 'lucide-react';

const mockFeedEvents = [
  {
    id: '1',
    timestamp: new Date().toISOString(),
    feed_type: 'control',
    volume: 0.5,
    notes: 'Regular feed cycle'
  },
  {
    id: '2',
    timestamp: new Date(Date.now() - 1800000).toISOString(),
    feed_type: 'experimental',
    volume: 0.75,
    notes: 'Increased volume test'
  }
];

export default function FeedEventsList() {
  return (
    <div className="space-y-4">
      {mockFeedEvents.map((event) => (
        <div
          key={event.id}
          className="flex items-start space-x-4 p-4 rounded-lg bg-gray-50 dark:bg-gray-700/50"
        >
          <div className="p-2 bg-blue-100 dark:bg-blue-900/50 rounded-full">
            <Beaker className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
              {event.feed_type === 'control' ? 'Control Feed' : 'Experimental Feed'}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Volume: {event.volume}L
            </p>
            {event.notes && (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {event.notes}
              </p>
            )}
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
              {format(new Date(event.timestamp), 'MMM d, yyyy HH:mm:ss')}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}