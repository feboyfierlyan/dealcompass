const paths = {
  compass: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm4 5-2.5 5.5L8 16l2.5-5.5L16 8Z',
  grid: 'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z',
  arrow: 'M5 12h14m-6-6 6 6-6 6',
  back: 'M19 12H5m6 6-6-6 6-6',
  refresh: 'M20 7v5h-5M4 17v-5h5M6 7a7 7 0 0 1 11-2l3 7M4 12l3 7a7 7 0 0 0 11-2',
  graph: 'M7 12h10M6 10V5h12v5M6 14v5h12v-5M4 10h4v4H4zM16 10h4v4h-4z',
  file: 'M14 3H5v18h14V8l-5-5Zm0 0v6h5M8 13h8M8 17h5',
  clock: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm0 4v5l3 2',
  search: 'M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14Zm5 12 6 6',
  chevron: 'm9 5 7 7-7 7',
  info: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm0 7v7m0-11v1',
  check: 'm5 12 4 4L19 6',
  target: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm0 5a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z',
  close: 'M6 6l12 12M18 6 6 18',
  alert: 'M12 4 2.8 19.5h18.4L12 4Zm0 6v4.5m0 2.5v.5',
  user: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm-7 8a7 7 0 0 1 14 0',
  flag: 'M5 21V4m0 0h11l-2 4 2 4H5',
  quote: 'M9 7H5v6h4v4l-2 2m10-12h-4v6h4v4l-2 2',
  history: 'M3 12a9 9 0 1 0 3-6.7M3 4v4h4m5-1v5l3 2',
  plus: 'M12 5v14M5 12h14',
  minus: 'M5 12h14',
  bot: 'M12 4v3M7 7h10a3 3 0 0 1 3 3v6a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3v-6a3 3 0 0 1 3-3Zm2 6v1m6-1v1M9 16h6',
  send: 'M12 19V5m-6 6 6-6 6 6',
  table: 'M4 5h16v14H4zM4 10h16M10 10v9',
  spark: 'M12 3v4m0 10v4M3 12h4m10 0h4M6 6l2.5 2.5m7 7L18 18M6 18l2.5-2.5m7-7L18 6',
};
export type IconName = keyof typeof paths;
export function Icon({ name, size = 20 }: { name: IconName; size?: number }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false"><path d={paths[name]}/></svg>;
}
