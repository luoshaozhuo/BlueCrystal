export type MarkovMatrixMode = 'difference' | 'baseline' | 'optimized';

export interface MatrixCountData {
  baseline?: number[][];
  optimized?: number[][];
}

export interface MarkovMatrixComparisonData {
  meanBins: string[];
  amplitudeBins: string[];
  baseline: number[][];
  optimized: number[][];
  counts?: MatrixCountData;
}

export const markovMatrixMockData: MarkovMatrixComparisonData = {
  meanBins: ['0-10', '10-20', '20-30', '30-40', '40-50', '50-60'],
  amplitudeBins: ['0-20', '20-40', '40-60', '60-80', '80-100', '100-120'],
  baseline: [
    [0.0092, 0.0149, 0.0172, 0.001, 0.0029, 0.0265],
    [0.0118, 0.0196, 0.0219, 0.0072, 0.0069, 0.0037],
    [0.0145, 0.0214, 0.0173, 0.0206, 0.0189, 0.0249],
    [0.0097, 0.0125, 0.0045, 0.0278, 0.0207, 0.0389],
    [0.0051, 0.0069, 0.001, 0.0199, 0.0151, 0.0078],
    [0.0024, 0.0034, 0.0009, 0.0098, 0.0075, 0.0047],
  ],
  optimized: [
    [0.0081, 0.0128, 0.0202, 0.0005, 0.0086, 0.0312],
    [0.0115, 0.018, 0.0256, 0.01, 0.0001, 0.0107],
    [0.0139, 0.0205, 0.0233, 0.0255, 0.0282, 0.0342],
    [0.0088, 0.011, 0.0096, 0.0353, 0.0154, 0.0336],
    [0.0056, 0.0064, 0.004, 0.0256, 0.0129, 0.0049],
    [0.0034, 0.0023, 0.0033, 0.0102, 0.0098, 0.007],
  ],
};
