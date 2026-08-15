import type { EvidenceMetricSource } from './optimization-evidence';

export type LoadMetricKey =
  | 'bladeRootMoment'
  | 'nacelleAcceleration'
  | 'generatorTorque';

export const loadMitigationTurbineOptions = [
  { label: 'WT-07', value: 'WT-07' },
  { label: 'WT-12', value: 'WT-12' },
  { label: 'WT-18', value: 'WT-18' },
];

export const loadMitigationTurbineMeta = {
  model: 'B123-5MW',
  commissionedAt: '2022-03-18',
  optimizedAt: '2024-07-01',
  windowDays: 180,
};

export const loadMitigationKpiList = [
  { key: 'blade_root_fatigue', trend: '↓', value: '12.4%' },
  { key: 'drive_train_fatigue', trend: '↓', value: '15.3%' },
  { key: 'nacelle_fatigue', trend: '↓', value: '9.1%' },
  { key: 'nacelle_vibration_rms', trend: '↓', value: '8.6%' },
  { key: 'nacelle_vibration_peak', trend: '↓', value: '6.8%' },
  { key: 'blade_root_moment_rms', trend: '↓', value: '7.4%' },
  { key: 'blade_root_moment_peak', trend: '↓', value: '5.9%' },
  { key: 'generator_torque_rms', trend: '↓', value: '7.2%' },
  { key: 'generator_torque_peak', trend: '↓', value: '6.1%' },
];

export const loadMitigationRangeBins = ['0-20', '20-40', '40-60', '60-80', '80-100', '100-120'];
export const loadMitigationMeanBins = ['0-10', '10-20', '20-30', '30-40', '40-50', '50-60'];
export const loadMitigationHighAmplitudeBins = ['40-50', '50-60'];

export const loadMitigationMetricSources: Record<LoadMetricKey, EvidenceMetricSource> = {
  bladeRootMoment: {
    metricKey: 'blade_root_moment',
    rmsWindowLabels: ['0.5s', '1s', '2s', '5s', '10s', '20s'],
    baselineMatrix: [[6, 10, 15, 18, 11, 5], [9, 17, 26, 32, 18, 8], [12, 24, 38, 46, 27, 12], [8, 19, 33, 41, 24, 10], [5, 12, 22, 27, 16, 7], [2, 6, 11, 14, 8, 4]],
    optimizedMatrix: [[10, 16, 22, 16, 8, 3], [14, 25, 34, 24, 12, 5], [18, 32, 42, 29, 14, 6], [12, 23, 31, 21, 10, 4], [7, 14, 19, 13, 6, 2], [3, 7, 10, 7, 3, 1]],
    baselineDamage: [0.02, 0.03, 0.05, 0.08, 0.12, 0.17, 0.23, 0.31, 0.4, 0.5, 0.61, 0.73, 0.86, 0.98, 1.07, 1.14, 1.18, 1.2, 1.19, 1.15, 1.09, 1.01, 0.92, 0.82, 0.71, 0.6, 0.5, 0.4, 0.31, 0.24, 0.18, 0.13, 0.09, 0.06, 0.04],
    optimizedDamage: [0.03, 0.04, 0.06, 0.09, 0.13, 0.18, 0.24, 0.32, 0.41, 0.51, 0.6, 0.69, 0.78, 0.86, 0.94, 1.01, 1.08, 1.14, 1.18, 1.2, 1.19, 1.15, 1.08, 0.99, 0.87, 0.74, 0.6, 0.47, 0.35, 0.26, 0.18, 0.12, 0.08, 0.05, 0.03],
    measurementUnit: 'MNm',
    measurementBase: 18,
    measurementScale: 23,
    measurementSpread: 2.8,
    baselineShock: [8.8, 11.4, 13.1, 12.4, 10.8, 9.1, 7.6, 6.2, 5.1],
    optimizedShock: [7.2, 9.4, 10.8, 10.1, 8.9, 7.6, 6.5, 5.4, 4.5],
  },
  nacelleAcceleration: {
    metricKey: 'nacelle_acceleration',
    rmsWindowLabels: ['0.5s', '1s', '2s', '5s', '10s', '20s'],
    baselineMatrix: [[4, 8, 12, 15, 13, 8], [6, 13, 21, 29, 24, 15], [8, 18, 31, 42, 35, 21], [6, 15, 28, 38, 31, 19], [4, 10, 19, 27, 22, 13], [2, 5, 10, 15, 12, 7]],
    optimizedMatrix: [[5, 9, 14, 18, 16, 10], [8, 16, 24, 31, 28, 18], [11, 22, 34, 43, 39, 24], [8, 18, 30, 37, 32, 20], [5, 11, 18, 22, 18, 11], [2, 5, 8, 10, 8, 5]],
    baselineDamage: [0.01, 0.02, 0.03, 0.05, 0.08, 0.12, 0.18, 0.26, 0.37, 0.5, 0.64, 0.78, 0.93, 1.08, 1.21, 1.31, 1.38, 1.42, 1.42, 1.38, 1.3, 1.2, 1.08, 0.94, 0.79, 0.64, 0.5, 0.37, 0.27, 0.19, 0.13, 0.08, 0.05, 0.03, 0.02],
    optimizedDamage: [0.01, 0.02, 0.04, 0.06, 0.09, 0.14, 0.21, 0.3, 0.42, 0.56, 0.7, 0.84, 0.96, 1.06, 1.13, 1.18, 1.2, 1.19, 1.15, 1.08, 0.99, 0.88, 0.76, 0.63, 0.5, 0.39, 0.3, 0.22, 0.15, 0.1, 0.06, 0.04, 0.03, 0.02, 0.01],
    measurementUnit: 'm/s^2',
    measurementBase: 0.08,
    measurementScale: 0.24,
    measurementSpread: 0.028,
    baselineShock: [5.6, 7.1, 8.3, 7.8, 6.9, 6.1, 5.2, 4.4, 3.6],
    optimizedShock: [4.7, 5.9, 6.8, 6.4, 5.8, 5.0, 4.3, 3.7, 3.0],
  },
  generatorTorque: {
    metricKey: 'generator_torque',
    rmsWindowLabels: ['0.5s', '1s', '2s', '5s', '10s', '20s'],
    baselineMatrix: [[5, 11, 18, 23, 17, 9], [7, 15, 26, 33, 25, 13], [9, 20, 35, 44, 33, 17], [7, 16, 29, 37, 27, 14], [4, 10, 18, 24, 17, 9], [2, 5, 9, 12, 8, 4]],
    optimizedMatrix: [[4, 9, 15, 21, 19, 11], [6, 13, 22, 29, 27, 16], [8, 18, 29, 38, 35, 21], [6, 14, 24, 30, 27, 16], [4, 9, 15, 19, 17, 10], [2, 4, 7, 9, 8, 5]],
    baselineDamage: [0.02, 0.03, 0.04, 0.07, 0.1, 0.14, 0.2, 0.27, 0.36, 0.47, 0.59, 0.72, 0.85, 0.98, 1.09, 1.18, 1.24, 1.27, 1.27, 1.23, 1.15, 1.05, 0.93, 0.8, 0.66, 0.53, 0.41, 0.31, 0.23, 0.16, 0.11, 0.07, 0.05, 0.03, 0.02],
    optimizedDamage: [0.02, 0.02, 0.03, 0.05, 0.08, 0.12, 0.17, 0.24, 0.33, 0.44, 0.56, 0.7, 0.84, 0.97, 1.08, 1.16, 1.2, 1.22, 1.2, 1.15, 1.06, 0.96, 0.84, 0.71, 0.58, 0.46, 0.35, 0.26, 0.19, 0.13, 0.09, 0.06, 0.04, 0.02, 0.01],
    measurementUnit: 'kNm',
    measurementBase: 6.5,
    measurementScale: 6.8,
    measurementSpread: 0.75,
    baselineShock: [9.4, 12.0, 13.8, 13.0, 11.5, 9.9, 8.3, 6.8, 5.5],
    optimizedShock: [7.9, 10.1, 11.6, 10.9, 9.7, 8.4, 7.1, 5.9, 4.8],
  },
};
