import { useEffect, useRef } from "react";

export default function EvidenceDownload({
  blob,
  id,
}: {
  blob: Blob;
  id: string;
}) {
  const link = useRef<HTMLAnchorElement>(null);
  useEffect(() => {
    const url = URL.createObjectURL(blob);
    link.current?.setAttribute("href", url);
    return () => URL.revokeObjectURL(url);
  }, [blob]);
  return (
    <a ref={link} download={`private-evidence-${id}.bin`}>
      Download inspected bytes
    </a>
  );
}
