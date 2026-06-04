import { computed, onBeforeUnmount, onMounted, reactive } from 'vue';

export const CHART_COMPARISON_COLORS = {
  baseline: '#8B95A7',
  optimized: '#19C2C9',
  accent: '#C9864A',
} as const;

export const CHART_SERIES_COLORS = [
  CHART_COMPARISON_COLORS.baseline,
  CHART_COMPARISON_COLORS.optimized,
  CHART_COMPARISON_COLORS.accent,
  '#6C7EE1',
  '#5FAF7B',
  '#D66B8F',
  '#4C9BCE',
  '#C2A34A',
] as const;

export const CHART_AUXILIARY_COLORS = {
  axisLineSoft: 'rgba(115, 142, 170, 0.45)',
  splitLineSoft: 'rgba(120, 157, 204, 0.08)',
  splitLineFaint: 'rgba(120, 157, 204, 0.05)',
  markerLine: 'rgba(120, 157, 204, 0.28)',
  markerFill: 'rgba(120, 157, 204, 0.12)',
  panelBorder: 'rgba(120, 157, 204, 0.12)',
  panelBorderStrong: 'rgba(120, 157, 204, 0.14)',
  panelBg: 'rgba(16, 30, 50, 0.32)',
  panelBgStrong: 'rgba(16, 30, 50, 0.34)',
  panelBgSoft: 'rgba(16, 30, 50, 0.24)',
  focusTextDark: '#0f1726',
  focusTextLight: '#e8f3ff',
  white: '#FFFFFF',
  lidarBlue: '#4CC9FF',
  lidarBlueSoft: '#49C7FF',
  lidarCyan: '#46E0C2',
  lidarAmber: '#F6C768',
  lidarAxisText: '#8CA6C1',
  lidarAxisTextStrong: '#93AEC9',
} as const;

export function withAlpha(color: string, alpha: number) {
  if (color.startsWith('#')) {
    const hex = color.slice(1);
    const normalized = hex.length === 3
      ? hex.split('').map((char) => `${char}${char}`).join('')
      : hex;
    const r = Number.parseInt(normalized.slice(0, 2), 16);
    const g = Number.parseInt(normalized.slice(2, 4), 16);
    const b = Number.parseInt(normalized.slice(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  if (color.startsWith('rgb(')) {
    return color.replace('rgb(', 'rgba(').replace(')', `, ${alpha})`);
  }

  return color;
}

interface ThemeTokens {
  text1: string;
  text2: string;
  text3: string;
  text4: string;
  fill2: string;
  fill3: string;
  border2: string;
  bg2: string;
  primary6: string;
  primary5: string;
  primary4: string;
  success4: string;
  warning4: string;
  danger4: string;
  danger6: string;
  tooltipBg: string;
  tooltipBorder: string;
  tooltipText: string;
  tooltipBgDark: string;
  tooltipBorderDark: string;
  tooltipTextLight: string;
  tooltipTextStyle: {
    color: string;
    fontSize: number;
    fontWeight: number;
    lineHeight: number;
  };
  splitLineSoft: string;
  splitLineFaint: string;
  markerLine: string;
  markerFill: string;
  panelBgSoft: string;
  panelBgStrong: string;
  focusTextDark: string;
  focusTextLight: string;
}

function getThemeRoots() {
  if (typeof window === 'undefined') return [];
  return [document.documentElement, document.body].filter(
    (element): element is HTMLElement => Boolean(element),
  );
}

function readCssVar(name: string, fallback = '') {
  const roots = getThemeRoots();
  for (const root of roots) {
    const value = getComputedStyle(root).getPropertyValue(name).trim();
    if (value) return value;
  }
  return fallback;
}

function readCssRgbVar(name: string, fallback = '') {
  const value = readCssVar(name);
  return value ? `rgb(${value})` : fallback;
}

export function useThemeTokens() {
  const tokens = reactive<ThemeTokens>({
    text1: '',
    text2: '',
    text3: '',
    text4: '',
    fill2: '',
    fill3: '',
    border2: '',
    bg2: '',
    primary6: '',
    primary5: '',
    primary4: '',
    success4: '',
    warning4: '',
    danger4: '',
    danger6: '',
    tooltipBg: '',
    tooltipBorder: '',
    tooltipText: '',
    tooltipBgDark: '',
    tooltipBorderDark: '',
    tooltipTextLight: '',
    tooltipTextStyle: {
      color: '',
      fontSize: 11,
      fontWeight: 400,
      lineHeight: 16,
    },
    splitLineSoft: CHART_AUXILIARY_COLORS.splitLineSoft,
    splitLineFaint: CHART_AUXILIARY_COLORS.splitLineFaint,
    markerLine: CHART_AUXILIARY_COLORS.markerLine,
    markerFill: CHART_AUXILIARY_COLORS.markerFill,
    panelBgSoft: CHART_AUXILIARY_COLORS.panelBgSoft,
    panelBgStrong: CHART_AUXILIARY_COLORS.panelBgStrong,
    focusTextDark: CHART_AUXILIARY_COLORS.focusTextDark,
    focusTextLight: CHART_AUXILIARY_COLORS.focusTextLight,
  });

  let observers: MutationObserver[] = [];

  function syncTokens() {
    const text1 = readCssVar('--color-text-1', '#1f2937');
    const text2 = readCssVar('--color-text-2', '#4e5969');
    const text3 = readCssVar('--color-text-3', '#86909c');
    const text4 = readCssVar('--color-text-4', '#c9cdd4');

    tokens.text1 = text1;
    tokens.text2 = text2 || text1;
    tokens.text3 = text3 || text2 || text1;
    tokens.text4 = text4 || text3 || text2 || text1;
    tokens.fill2 = readCssVar('--color-fill-2', '#f2f3f5');
    tokens.fill3 = readCssVar('--color-fill-3', '#e5e6eb');
    tokens.border2 = readCssVar('--color-border-2', '#c9cdd4');
    tokens.bg2 = readCssVar('--color-bg-2', '#f7f8fa');
    tokens.primary6 = readCssRgbVar('--primary-6', '#3c7eff');
    tokens.primary5 = readCssVar('--color-primary-light-5', '#6aa1ff');
    tokens.primary4 = readCssVar('--color-primary-light-4', '#3c7eff');
    tokens.success4 = readCssVar('--color-success-light-4', '#00b42a');
    tokens.warning4 = readCssVar('--color-warning-light-4', '#ff7d00');
    tokens.danger4 = readCssVar('--color-danger-light-4', '#f53f3f');
    tokens.danger6 = readCssRgbVar('--danger-6', readCssVar('--color-danger-6', tokens.danger4));
    tokens.tooltipBg = tokens.bg2;
    tokens.tooltipBorder = tokens.border2;
    tokens.tooltipText = tokens.text2;
    tokens.tooltipBgDark = tokens.tooltipBg;
    tokens.tooltipBorderDark = tokens.tooltipBorder;
    tokens.tooltipTextLight = tokens.tooltipText;
    tokens.tooltipTextStyle = {
      color: tokens.tooltipText,
      fontSize: 11,
      fontWeight: 400,
      lineHeight: 16,
    };
    tokens.splitLineSoft = CHART_AUXILIARY_COLORS.splitLineSoft;
    tokens.splitLineFaint = CHART_AUXILIARY_COLORS.splitLineFaint;
    tokens.markerLine = CHART_AUXILIARY_COLORS.markerLine;
    tokens.markerFill = CHART_AUXILIARY_COLORS.markerFill;
    tokens.panelBgSoft = CHART_AUXILIARY_COLORS.panelBgSoft;
    tokens.panelBgStrong = CHART_AUXILIARY_COLORS.panelBgStrong;
    tokens.focusTextDark = CHART_AUXILIARY_COLORS.focusTextDark;
    tokens.focusTextLight = CHART_AUXILIARY_COLORS.focusTextLight;
  }

  onMounted(() => {
    syncTokens();

    observers = getThemeRoots().map((root) => {
      const observer = new MutationObserver(() => {
        syncTokens();
      });
      observer.observe(root, {
        attributes: true,
        attributeFilter: ['style', 'class', 'arco-theme', 'data-theme'],
      });
      return observer;
    });
  });

  onBeforeUnmount(() => {
    observers.forEach((observer) => observer.disconnect());
    observers = [];
  });

  return tokens;
}

export function useChartTheme() {
  const tokens = useThemeTokens();

  return computed(() => ({
    textStrong: tokens.text1,
    textMain: tokens.text2,
    textMuted: tokens.text3,
    textFaint: tokens.text4,
    bgPanel: tokens.bg2,
    fillSoft: tokens.fill2,
    fillMuted: tokens.fill3,
    borderSoft: tokens.border2,
    tooltipBg: tokens.tooltipBg,
    tooltipBorder: tokens.tooltipBorder,
    tooltipText: tokens.tooltipText,
    tooltipTextStyle: tokens.tooltipTextStyle,
    axisLine: tokens.border2,
    splitLine: tokens.fill3,
    primary: tokens.primary4,
    primaryStrong: tokens.primary6,
    success: tokens.success4,
    warning: tokens.warning4,
    danger: tokens.danger4,
    info: tokens.primary5,
    tooltipBgDark: tokens.tooltipBg,
    tooltipBorderDark: tokens.tooltipBorder,
    tooltipTextLight: tokens.tooltipText,
    axisLineSoft: CHART_AUXILIARY_COLORS.axisLineSoft,
    splitLineSoft: CHART_AUXILIARY_COLORS.splitLineSoft,
    splitLineFaint: CHART_AUXILIARY_COLORS.splitLineFaint,
    markerLine: CHART_AUXILIARY_COLORS.markerLine,
    markerFill: CHART_AUXILIARY_COLORS.markerFill,
    panelBorder: CHART_AUXILIARY_COLORS.panelBorder,
    panelBorderStrong: CHART_AUXILIARY_COLORS.panelBorderStrong,
    panelBg: CHART_AUXILIARY_COLORS.panelBg,
    panelBgStrong: CHART_AUXILIARY_COLORS.panelBgStrong,
    panelBgSoft: CHART_AUXILIARY_COLORS.panelBgSoft,
    focusTextDark: CHART_AUXILIARY_COLORS.focusTextDark,
    focusTextLight: CHART_AUXILIARY_COLORS.focusTextLight,
    lidarBlue: CHART_AUXILIARY_COLORS.lidarBlue,
    lidarBlueSoft: CHART_AUXILIARY_COLORS.lidarBlueSoft,
    lidarCyan: CHART_AUXILIARY_COLORS.lidarCyan,
    lidarAmber: CHART_AUXILIARY_COLORS.lidarAmber,
    lidarAxisText: CHART_AUXILIARY_COLORS.lidarAxisText,
    lidarAxisTextStrong: CHART_AUXILIARY_COLORS.lidarAxisTextStrong,
    titleTextStyle: {
      color: tokens.text2,
      fontSize: 12,
      fontWeight: 500,
      lineHeight: 16,
    },
    infoTextStyle: {
      color: tokens.text3,
      fontSize: 11,
      fontWeight: 400,
      lineHeight: 14,
    },
    legendTextStyle: {
      color: tokens.text3,
      fontSize: 10,
    },
    axisNameTextStyle: {
      color: tokens.text3,
      fontSize: 10,
    },
    axisLabelTextStyle: {
      color: tokens.text3,
      fontSize: 10,
    },
    comparisonColors: CHART_COMPARISON_COLORS,
    seriesColors: CHART_SERIES_COLORS,
    semanticColors: {
      primary: tokens.primary4,
      primaryStrong: tokens.primary6,
      success: tokens.success4,
      warning: tokens.warning4,
      danger: tokens.danger4,
      info: tokens.primary5,
      dangerStrong: tokens.danger6,
    },
    visualMapColors: [
      readCssVar('--color-fill-4', '#d0d3d6'),
      readCssVar('--color-primary-light-6', '#8db3ff'),
      tokens.primary5,
      tokens.success4,
      readCssVar('--color-warning-light-5', '#ffb65d'),
    ],
  }));
}
