import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { format } from 'date-fns';
import { useStore } from '../../store/useStore';

const formatTimestamp = (timestamp: string) => {
  return format(new Date(timestamp), 'HH:mm:ss');
};

export default function MetricsChart() {
  const { metrics } = useStore();
  const [data, setData] = React.useState<Array<any>>([]);

  React.useEffect(() => {
    if (metrics) {
      setData(prevData => {
        const newData = [...prevData, {
          timestamp: metrics.timestamp,
          doSaturation: metrics.do_saturation,
          dropRate: metrics.drop_rate,
          our: metrics.our,
          temperature: metrics.temperature
        }].slice(-60); // Keep last 60 data points
        return newData;
      });
    }
  }, [metrics]);

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="timestamp"
          tickFormatter={formatTimestamp}
          interval="preserveEnd"
        />
        <YAxis yAxisId="left" />
        <YAxis yAxisId="right" orientation="right" />
        <Tooltip
          labelFormatter={formatTimestamp}
          contentStyle={{
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
            border: '1px solid #ccc'
          }}
        />
        <Legend />
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="doSaturation"
          name="DO Saturation (%)"
          stroke="#2563eb"
          dot={false}
        />
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="dropRate"
          name="Drop Rate"
          stroke="#16a34a"
          dot={false}
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="our"
          name="OUR"
          stroke="#9333ea"
          dot={false}
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="temperature"
          name="Temperature (°C)"
          stroke="#dc2626"
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}