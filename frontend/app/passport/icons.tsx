type IconName =
  | "grid"
  | "create"
  | "scan"
  | "shield"
  | "passport"
  | "arrow"
  | "spark"
  | "search"
  | "history"
  | "refresh"
  | "command"
  | "pulse"
  | "close"
  | "menu"
  | "check"
  | "file"
  | "portrait"
  | "settings";
const paths: Record<IconName, string> = {
  settings: "M4 6h16 M4 12h16 M4 18h16 M8 3v6 M16 9v6 M10 15v6",
  portrait: "M12 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8 M4 21v-2a8 8 0 0 1 16 0v2",
  grid: "M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z",
  create: "M12 4v16 M4 12h16",
  scan: "M3 8V3h5 M16 3h5v5 M21 16v5h-5 M8 21H3v-5 M3 12h18",
  shield: "M12 3l8 3v6c0 5-8 9-8 9s-8-4-8-9V6z",
  passport: "M5 3h14v18H5z M9 7h6 M9 17h6 M8 12h8",
  arrow: "M5 12h14 M13 6l6 6-6 6",
  spark: "M12 3l2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5z",
  search: "M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14 M15 15l6 6",
  history: "M3 4v6h6 M3 10a9 9 0 1 1 1 8 M12 7v5l4 2",
  refresh: "M20 7v5h-5 M4 17v-5h5 M6 6a8 8 0 0 1 14 6 M18 18a8 8 0 0 1-14-6",
  command:
    "M9 7V5a2 2 0 1 0-2 2h10a2 2 0 1 0-2-2v14a2 2 0 1 0 2-2H7a2 2 0 1 0 2 2V7",
  pulse: "M2 12h5l3-8 4 16 3-8h5",
  close: "M5 5l14 14 M19 5L5 19",
  menu: "M3 6h18 M3 12h18 M3 18h18",
  check: "M4 12l5 5L20 6",
  file: "M6 3h8l4 4v14H6z M14 3v5h4 M9 12h6 M9 16h6",
};
export default function Icon({
  name,
  size = 18,
}: {
  name: IconName;
  size?: number;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className="icon"
    >
      <path d={paths[name]} />
    </svg>
  );
}
