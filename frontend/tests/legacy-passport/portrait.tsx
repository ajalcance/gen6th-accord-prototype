export default function Portrait({ variant = 0 }: { variant?: number }) {
  return (
    <svg
      viewBox="0 0 400 480"
      role="img"
      aria-label="Original fictional persona illustration"
    >
      <rect
        width="400"
        height="480"
        fill={["#9bb7bd", "#baabce", "#d4ac83"][variant % 3]}
      />
      <circle cx="310" cy="90" r="130" fill="#fff" opacity=".14" />
      <path d="M35 480Q45 320 200 318Q355 320 370 480" fill="#222a32" />
      <path d="M165 280L165 338Q200 370 235 338L235 280" fill="#bb8268" />
      <path
        d="M108 200Q85 50 208 51Q320 50 293 233L274 322L123 300Z"
        fill="#22272b"
      />
      <ellipse cx="201" cy="201" rx="82" ry="112" fill="#d7a58a" />
      <path
        d="M114 192Q107 60 211 70Q293 70 289 180Q246 140 219 105Q184 170 114 192"
        fill="#24282b"
      />
      <path
        d="M148 194Q163 186 179 194M224 194Q241 186 256 194"
        fill="none"
        stroke="#45352f"
        strokeWidth="5"
        strokeLinecap="round"
      />
      <path
        d="M199 206L191 240L207 241"
        fill="none"
        stroke="#b37c65"
        strokeWidth="3"
      />
      <path d="M174 263Q202 276 229 260Q202 293 174 263" fill="#955b55" />
      <path d="M73 480L133 351L199 399L267 351L331 480" fill="#e0e2df" />
      <path
        d="M133 351L164 335L199 399L158 424ZM267 351L236 335L199 399L242 424Z"
        fill="#faf7ef"
      />
      <text x="24" y="453" fill="#fff" fontSize="11" letterSpacing="3">
        FICTIONAL · VECTOR STUDY
      </text>
    </svg>
  );
}
