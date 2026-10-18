import type { PointerEvent } from "react";
import Portrait from "./portrait";
import type { StudioState } from "./use-studio";

export default function PaletteComparison(props: StudioState) {
  return (
    <section className="comparison" aria-label="Palette comparison">
      <div className="comparison-heading">
        <h3>Compare supplied studies</h3>
        <span>Canonical ↔ altered palette</span>
      </div>
      <ComparisonCanvas {...props} />
      <label>
        Palette comparison · illustrative only
        <input
          type="range"
          min="0"
          max="100"
          value={props.comparison}
          onChange={(event) => props.setComparison(Number(event.target.value))}
          aria-valuetext={`${props.comparison}% canonical study`}
        />
      </label>
      <p className="help">
        Drag across the image or use the slider and arrow keys. Shared drawing,
        different palette; no similarity score is computed.
      </p>
    </section>
  );
}

function ComparisonCanvas(props: StudioState) {
  function update(event: PointerEvent<HTMLDivElement>) {
    const bounds = event.currentTarget.getBoundingClientRect();
    if (bounds.width > 0)
      props.setComparison(
        Math.round(((event.clientX - bounds.left) / bounds.width) * 100),
      );
  }
  return (
    <div
      className="compare-images"
      onPointerDown={(event) => {
        if (event.button !== 0) return;
        event.currentTarget.setPointerCapture(event.pointerId);
        update(event);
      }}
      onPointerMove={(event) => {
        if (event.currentTarget.hasPointerCapture(event.pointerId))
          update(event);
      }}
      onPointerUp={(event) => {
        if (event.currentTarget.hasPointerCapture(event.pointerId))
          event.currentTarget.releasePointerCapture(event.pointerId);
      }}
    >
      <Portrait variant={props.variant} />
      <div
        className="compare-overlay"
        style={{ clipPath: `inset(0 0 0 ${props.comparison}%)` }}
      >
        <Portrait variant={(props.variant + 1) % 3} />
      </div>
      <div
        className="compare-divider"
        style={{ left: `${props.comparison}%` }}
        aria-hidden="true"
      >
        <span>↔</span>
      </div>
      <span className="compare-label left">CANONICAL</span>
      <span className="compare-label right">PALETTE STUDY</span>
    </div>
  );
}
