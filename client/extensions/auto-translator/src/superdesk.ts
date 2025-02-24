import { ISuperdesk } from "superdesk-api";
import { WIDGET_ID } from "./constants";

// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
export const superdesk = window["extensionsApiInstances"][
  WIDGET_ID
] as ISuperdesk;
