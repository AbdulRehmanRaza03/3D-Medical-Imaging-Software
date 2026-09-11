/** Lightweight inline SVG icon set (stroke-based, no external dependency). */

import type { SVGProps } from "react";

type P = SVGProps<SVGSVGElement>;

const base = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.75,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  viewBox: "0 0 24 24",
};

export function IconLogo(props: P) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M7 3h10v4a5 5 0 01-10 0V3z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6M12 9v6" />
      <rect x="5" y="15" width="14" height="6" rx="1.5" />
    </svg>
  );
}

export function IconUpload(props: P) {
  return (
    <svg {...base} {...props}>
      <path d="M12 16V4m0 0l-4 4m4-4l4 4" />
      <path d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2" />
    </svg>
  );
}

export function IconGrid(props: P) {
  return (
    <svg {...base} {...props}>
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
      <rect x="14" y="14" width="7" height="7" rx="1.5" />
    </svg>
  );
}

export function IconCube(props: P) {
  return (
    <svg {...base} {...props}>
      <path d="M12 2l8 4.5v9L12 20l-8-4.5v-9L12 2z" />
      <path d="M12 11l8-4.5M12 11L4 6.5M12 11v9" />
    </svg>
  );
}

export function IconRuler(props: P) {
  return (
    <svg {...base} {...props}>
      <path d="M3 17l11-11 4 4-11 11-4-4z" />
      <path d="M6.5 13.5l1.5 1.5M9.5 10.5l1.5 1.5M12.5 7.5l1.5 1.5" />
    </svg>
  );
}

export function IconDownload(props: P) {
  return (
    <svg {...base} {...props}>
      <path d="M12 4v10m0 0l-4-4m4 4l4-4" />
      <path d="M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2" />
    </svg>
  );
}

export function IconScan(props: P) {
  return (
    <svg {...base} {...props}>
      <path d="M3 7V5a2 2 0 012-2h2M17 3h2a2 2 0 012 2v2M21 17v2a2 2 0 01-2 2h-2M7 21H5a2 2 0 01-2-2v-2" />
      <path d="M7 12h10" />
    </svg>
  );
}

export function IconLayers(props: P) {
  return (
    <svg {...base} {...props}>
      <path d="M12 3l9 5-9 5-9-5 9-5z" />
      <path d="M3 13l9 5 9-5" />
      <path d="M3 17l9 5 9-5" />
    </svg>
  );
}

export function IconClock(props: P) {
  return (
    <svg {...base} {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 3" />
    </svg>
  );
}

export function IconCheck(props: P) {
  return (
    <svg {...base} {...props}>
      <path d="M4 12l5 5L20 6" />
    </svg>
  );
}

export function IconAlert(props: P) {
  return (
    <svg {...base} {...props}>
      <path d="M12 3l9 17H3l9-17z" />
      <path d="M12 10v4M12 17.5v.5" />
    </svg>
  );
}

export function IconArrowRight(props: P) {
  return (
    <svg {...base} {...props}>
      <path d="M5 12h14m0 0l-6-6m6 6l-6 6" />
    </svg>
  );
}

export function IconArrowLeft(props: P) {
  return (
    <svg {...base} {...props}>
      <path d="M19 12H5m0 0l6-6m-6 6l6 6" />
    </svg>
  );
}

export function IconActivity(props: P) {
  return (
    <svg {...base} {...props}>
      <path d="M3 12h4l2-7 4 14 2-7h6" />
    </svg>
  );
}

export function IconRefresh(props: P) {
  return (
    <svg {...base} {...props}>
      <path d="M21 12a9 9 0 11-2.64-6.36M21 3v6h-6" />
    </svg>
  );
}

export function IconSliders(props: P) {
  return (
    <svg {...base} {...props}>
      <path d="M4 6h9M17 6h3M4 12h3M11 12h9M4 18h9M17 18h3" />
      <circle cx="15" cy="6" r="2" />
      <circle cx="9" cy="12" r="2" />
      <circle cx="15" cy="18" r="2" />
    </svg>
  );
}

export function IconSpinner(props: P) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" className="animate-spin" {...props}>
      <path d="M21 12a9 9 0 11-9-9" />
    </svg>
  );
}
