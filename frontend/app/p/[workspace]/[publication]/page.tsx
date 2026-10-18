import PublicPassport from "../../../passport/public-passport";

export default async function Page({
  params,
}: {
  params: Promise<{ workspace: string; publication: string }>;
}) {
  const { workspace, publication } = await params;
  return <PublicPassport workspace={workspace} publication={publication} />;
}
