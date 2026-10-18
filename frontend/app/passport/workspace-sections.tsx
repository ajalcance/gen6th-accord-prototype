export default function WorkspaceSections({
  items,
  selected,
  select,
  label,
}: {
  items: readonly string[];
  selected: string;
  select: (item: string) => void;
  label: string;
}) {
  return (
    <div className="workspace-tabs" role="group" aria-label={label}>
      {items.map((item) => (
        <button
          type="button"
          key={item}
          className="secondary"
          aria-pressed={selected === item}
          onClick={() => select(item)}
        >
          {item}
        </button>
      ))}
    </div>
  );
}
