import ConnectedWorkspace from "./passport/connected-workspace";

export const dynamic = "force-dynamic";

export default function Home() {
  return (
    <ConnectedWorkspace
      enabled={process.env.ACCORD_CONNECTION_ENABLED === "true"}
    />
  );
}
