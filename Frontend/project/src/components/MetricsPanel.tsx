import React from 'react';
import { useStore } from '../store/useStore';
import { Droplet, Thermometer, Activity, Timer } from 'lucide-react';

export default function MetricsPanel() {
  const { metrics } = useStore();

  if (!metrics) return null;

  const metricCards = [
    {
      icon: <Droplet className="text-blue-500" />,
      label: 'DO Saturation',
      value: `${metrics.do_saturation.toFixed(1)}%`,
    },
    {
      icon: <Activity className="text-green-500" />,
      label: 'Drop Rate',
      value: `${metrics.drop_rate.toFixed(2)} drops/min`,
    },
    {
      icon: <Timer className="text-purple-500" />,
      label: 'Recovery Time',
      value: `${metrics.recovery_time.toFixed(1)}s`,
    },
    {
      icon: <Thermometer className="text-red-500" />,
      label: 'Temperature',
      value: `${metrics.temperature.toFixed(1)}°C`,
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {metricCards.map((card) => (
        <div
          key={card.label}
          className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700"
        >
          <div className="flex items-center space-x-4">
            {card.icon}
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">{card.label}</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">{card.value}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}