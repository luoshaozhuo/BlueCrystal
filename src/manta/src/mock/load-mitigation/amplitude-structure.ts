export interface MeanBinDistribution {
  meanBin: string;
  values: number[];
}

export interface AmplitudeStructureComparisonData {
  meanBins: string[];
  amplitudeBins: string[];
  baseline: MeanBinDistribution[];
  optimized: MeanBinDistribution[];
}

export const amplitudeStructureMockData: AmplitudeStructureComparisonData = {
  meanBins: ['0-20', '20-40', '40-60', '60-80', '80-100', '100-120'],
  amplitudeBins: ['0-10', '10-20', '20-30', '30-40', '40-50', '50-60'],
  baseline: [
    { meanBin: '0-20', values: [0.35, 0.25, 0.18, 0.12, 0.07, 0.03] },
    { meanBin: '20-40', values: [0.3, 0.26, 0.2, 0.13, 0.08, 0.03] },
    { meanBin: '40-60', values: [0.24, 0.23, 0.2, 0.16, 0.11, 0.06] },
    { meanBin: '60-80', values: [0.2, 0.21, 0.2, 0.18, 0.14, 0.07] },
    { meanBin: '80-100', values: [0.17, 0.2, 0.19, 0.19, 0.16, 0.09] },
    { meanBin: '100-120', values: [0.15, 0.18, 0.19, 0.2, 0.18, 0.1] },
  ],
  optimized: [
    { meanBin: '0-20', values: [0.4, 0.27, 0.16, 0.1, 0.05, 0.02] },
    { meanBin: '20-40', values: [0.34, 0.28, 0.19, 0.11, 0.06, 0.02] },
    { meanBin: '40-60', values: [0.29, 0.25, 0.19, 0.14, 0.09, 0.04] },
    { meanBin: '60-80', values: [0.25, 0.23, 0.2, 0.16, 0.11, 0.05] },
    { meanBin: '80-100', values: [0.22, 0.22, 0.2, 0.17, 0.13, 0.06] },
    { meanBin: '100-120', values: [0.2, 0.21, 0.2, 0.18, 0.14, 0.07] },
  ],
};
