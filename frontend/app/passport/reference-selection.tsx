import Image from "next/image";

type Props = {
  ids: string[];
  change: (next: string[]) => void;
  previews: Map<string, string>;
};
export default function ReferenceSelection(props: Props) {
  return (
    <>
      <p>{props.ids.length} of 8 selected</p>
      <ol className="reference-selection">
        {props.ids.map((id, index) => (
          <SelectedReference key={id} {...props} id={id} index={index} />
        ))}
      </ol>
      <button
        type="button"
        className="secondary"
        disabled={!props.ids.length}
        onClick={() => props.change([])}
      >
        Clear all references
      </button>
    </>
  );
}
function SelectedReference({
  ids,
  change,
  previews,
  id,
  index,
}: Props & { id: string; index: number }) {
  const preview = previews.get(id);
  function earlier() {
    const next = [...ids];
    [next[index - 1], next[index]] = [next[index], next[index - 1]];
    change(next);
  }
  return (
    <li>
      {preview && (
        <Image
          className="reference-preview"
          src={preview}
          alt={`Unsaved reference ${index + 1} preview`}
          width={120}
          height={120}
          unoptimized
        />
      )}
      <span>
        Reference {index + 1} · {id}
      </span>{" "}
      <button
        type="button"
        className="secondary"
        disabled={index === 0}
        onClick={earlier}
      >
        Move reference {index + 1} earlier
      </button>{" "}
      <button
        type="button"
        className="secondary"
        onClick={() => change(ids.filter((item) => item !== id))}
      >
        Remove reference {index + 1}
      </button>
    </li>
  );
}
