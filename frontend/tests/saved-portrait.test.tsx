import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import SavedPhoto from "../app/passport/saved-photo";
import { preparedSource, version } from "./prepared-write-fixtures";
import { portraitGateway } from "./portrait-fixtures";

beforeEach(() => {
  vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:synthetic");
  vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => {});
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

it("marks an authorized confirmed missing portrait incomplete in records and details", async () => {
  const source = preparedSource();
  source.photos = portraitGateway(source.workspaceId);
  render(
    <SavedPhoto
      source={source}
      versionId={version.version_id}
      name="Synthetic persona"
    />,
  );
  expect(
    await screen.findByText("Incomplete — portrait required"),
  ).toBeDefined();
  expect(screen.queryByRole("img")).toBeNull();
});

it("does not confuse unavailable portrait services with a confirmed missing image", async () => {
  const source = preparedSource();
  source.photos = {
    ...portraitGateway(source.workspaceId),
    thumbnail: async () => {
      throw new Error("synthetic outage");
    },
  };
  render(
    <SavedPhoto
      source={source}
      versionId={version.version_id}
      name="Synthetic persona"
    />,
  );
  expect(await screen.findByText("Portrait status unavailable")).toBeDefined();
  expect(screen.queryByText(/Incomplete/)).toBeNull();
});

it("clears the old missing status while a replacement gateway is still loading", async () => {
  const source = preparedSource();
  source.photos = portraitGateway(source.workspaceId);
  const element = (value: typeof source) => (
    <SavedPhoto
      source={value}
      versionId={version.version_id}
      name="Synthetic persona"
    />
  );
  const mounted = render(element(source));
  await screen.findByText("Incomplete — portrait required");
  let finish: (blob: Blob | null) => void = () => {};
  mounted.rerender(
    element({
      ...source,
      photos: {
        ...portraitGateway(source.workspaceId),
        thumbnail: () =>
          new Promise((resolve) => {
            finish = resolve;
          }),
      },
    }),
  );
  expect(screen.getByText("Checking portrait…")).toBeDefined();
  expect(screen.queryByText(/Incomplete/)).toBeNull();
  await act(async () => finish(null));
  expect(screen.getByText("Incomplete — portrait required")).toBeDefined();
});

it("clears portrait completeness on session change and ignores the previous late result", async () => {
  const source = preparedSource();
  let finish: (blob: Blob | null) => void = () => {};
  source.photos = {
    ...portraitGateway(source.workspaceId),
    thumbnail: () =>
      new Promise((resolve) => {
        finish = resolve;
      }),
  };
  const mounted = render(
    <SavedPhoto
      source={source}
      versionId={version.version_id}
      name="Synthetic persona"
    />,
  );
  mounted.rerender(
    <SavedPhoto
      source={null}
      versionId={version.version_id}
      name="Synthetic persona"
    />,
  );
  await act(async () => finish(null));
  expect(screen.getByText("Portrait status unavailable")).toBeDefined();
  expect(screen.queryByText(/Incomplete/)).toBeNull();
});

it("shows a confirmed portrait without an incomplete label and releases its private preview", async () => {
  const source = preparedSource();
  source.photos = {
    ...portraitGateway(source.workspaceId),
    thumbnail: async () => new Blob(["synthetic"], { type: "image/png" }),
  };
  const mounted = render(
    <SavedPhoto
      source={source}
      versionId={version.version_id}
      name="Synthetic persona"
    />,
  );
  expect(
    await screen.findByAltText("Saved photo of Synthetic persona"),
  ).toBeDefined();
  expect(screen.queryByText(/Incomplete/)).toBeNull();
  mounted.unmount();
  expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:synthetic");
});
