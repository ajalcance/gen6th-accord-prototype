import Image from "next/image";
import type { FaceResult } from "../../lib/persona-faces";

export default function FacePreview({
  url,
  faces,
  alt = "Approved reference portrait",
}: {
  url: string;
  faces?: Pick<FaceResult, "width" | "height" | "faces">;
  alt?: string;
}) {
  return (
    <div
      className={faces ? "face-preview" : undefined}
      style={
        faces ? { aspectRatio: `${faces.width}/${faces.height}` } : undefined
      }
    >
      <Image
        className="reference-preview"
        src={url}
        alt={alt}
        width={120}
        height={120}
        unoptimized
      />
      {faces?.faces.map((face) => (
        <span
          aria-hidden="true"
          className="face-box"
          key={face.index}
          style={{
            left: `${(100 * face.x) / faces.width}%`,
            top: `${(100 * face.y) / faces.height}%`,
            width: `${(100 * face.width) / faces.width}%`,
            height: `${(100 * face.height) / faces.height}%`,
          }}
        >
          {face.index + 1}
        </span>
      ))}
    </div>
  );
}
