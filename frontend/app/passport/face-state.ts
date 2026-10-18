import { useContext, useMemo } from "react";
import type {
  FaceCommand,
  FaceGateway,
  FaceResult,
} from "../../lib/persona-faces";
import { PersonaMutation } from "../../lib/persona-mutation";
import {
  object,
  uuid,
  integer,
  requireContract,
} from "../../lib/persona-validation";
import {
  WriteDraftContext,
  useWriteLifecycle,
  type WriteCommand,
} from "./prepared-write-state";

function faceCommand(command: WriteCommand): FaceCommand {
  const r = object(command, [
    "version_id",
    "portrait_id",
    "request_id",
    "generation_id",
    "face_index",
  ]);
  const generation_id = r.generation_id === null ? null : uuid(r.generation_id);
  const face_index = r.face_index === null ? null : integer(r.face_index, 0);
  requireContract(
    (generation_id === null) === (face_index === null) &&
      (face_index === null || face_index <= 9),
  );
  return {
    version_id: uuid(r.version_id),
    portrait_id: uuid(r.portrait_id),
    request_id: uuid(r.request_id),
    generation_id,
    face_index,
  };
}
export function useFaceMutation(
  gateway: FaceGateway,
  key: string,
  denied: () => void,
) {
  const store = useContext(WriteDraftContext);
  const mutation = useMemo(
    () =>
      new PersonaMutation<WriteCommand, unknown>(
        (command, signal) => gateway.process(faceCommand(command), signal),
        store?.get(key)?.checkpoint ?? undefined,
        faceCommand,
      ),
    [gateway, key, store],
  );
  return useWriteLifecycle(mutation, store, key, denied);
}
export type FaceMutation = ReturnType<typeof useFaceMutation>;
export function resultReceipt(mutation: FaceMutation): FaceResult | null {
  return mutation.state.phase === "succeeded"
    ? (mutation.state.receipt as FaceResult)
    : null;
}
