import Image from "next/image";

const STEPS = ["Register a performer", "Add the evidence", "Issue a passport"];

/**
 * First screen for a visitor with no session. States what Accord is, offers the one action
 * that unlocks the workspace, and shows the real mark. The faded background is pure CSS
 * (branding.css), so the content security policy is unchanged.
 */
export default function SignedOutWelcome({ signIn }: { signIn?: () => void }) {
  return (
    <section className="welcome" aria-label="Saved records connection">
      <Image
        unoptimized
        className="welcome-logo"
        src="/brand/gen6th-accord-dark.svg"
        width={1580}
        height={360}
        alt="Gen6th Accord"
        priority
      />
      <h2>A registry and verifiable passport for AI performers</h2>
      <p>
        Accord records who made a performer, the evidence behind it and what its
        use is permitted for. Sign in to open your workspace.
      </p>
      <ol className="welcome-steps">
        {STEPS.map((step) => (
          <li key={step}>{step}</li>
        ))}
      </ol>
      {signIn ? (
        <button className="primary welcome-action" onClick={signIn}>
          Sign in to your workspace
        </button>
      ) : (
        <p className="help">Sign-in is not available right now.</p>
      )}
    </section>
  );
}
