import React from "react";
import {
  Line,
  Bar
} from "react-chartjs-2";

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Tooltip,
  Legend,
} from "chart.js";

// Register chart components that might be using
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Tooltip,
  Legend
);

// Mock grade progression trend chart 
export const AccuracyChart = () => {
  const data = {
    labels: ["Mon", "Tue", "Wed", "Thu", "Fri"],
    datasets: [
      {
        label: "Accuracy %",
        data: [60, 70, 65, 80, 75],
        tension: 0.4,
      },
    ],
  };

  return <Line data={data} />;
};
