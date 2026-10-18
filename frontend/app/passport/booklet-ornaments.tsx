export function BookletStar() {
  return (
    <svg viewBox="0 0 100 100" aria-hidden="true">
      <path d="M50 8L58 41L91 50L58 59L50 92L42 59L9 50L42 41Z" />
      <path d="M50 8V92M9 50H91" />
    </svg>
  );
}
export function BookletRule() {
  return (
    <div className="booklet-rule" aria-hidden="true">
      <span />
      <BookletStar />
      <span />
    </div>
  );
}
export function BookletSeal() {
  return (
    <div className="signature-seal" aria-hidden="true">
      <svg viewBox="0 0 120 120">
        <circle cx="60" cy="60" r="55" />
        <circle cx="60" cy="60" r="50" />
        <circle cx="60" cy="60" r="44" />
        <path d="M60 17L67 49L92 29L73 54L104 60L73 66L92 91L67 72L60 104L53 72L28 91L47 66L16 60L47 54L28 29L53 49Z" />
        <path d="M60 17V104M16 60H104M28 29L92 91M28 91L92 29" />
      </svg>
    </div>
  );
}
export function BookletQr({ modules }: { modules: boolean[][] }) {
  const size = modules.length + 8;
  const path = modules
    .flatMap((row, y) =>
      row.flatMap((dark, x) => (dark ? [`M${x + 4},${y + 4}h1v1h-1z`] : [])),
    )
    .join("");
  return (
    <div className="booklet-qr">
      <svg
        role="img"
        aria-label="QR code for approved public passport"
        viewBox={`0 0 ${size} ${size}`}
        shapeRendering="crispEdges"
      >
        <rect width={size} height={size} fill="white" />
        <path d={path} fill="#101e4d" />
      </svg>
    </div>
  );
}
export function BookletFooter({
  page,
  message,
}: {
  page: string;
  message: string;
}) {
  return (
    <footer className="page-footer">
      <span>{page}</span>
      <p>{message}</p>
      <BookletStar />
    </footer>
  );
}
