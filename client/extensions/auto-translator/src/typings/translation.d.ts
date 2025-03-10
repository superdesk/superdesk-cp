import { IBaseRestApiResponse } from "superdesk-api";
import { TRANSLATION_TYPES } from "../constants";

type TranslationImageField = `media-gallery--${number}`;

type TranslationFields = "headline" | "headline_extended" | "body_html";

type TranslationType = keyof typeof TRANSLATION_TYPES;

export type TranslationPayload = {
  body_html: "";
  payload: Record<TranslationFields, string> & {
    images?: Record<TranslationImageField, string>;
  };
  target_language: string;
  source_language: string;
  translation_type: TranslationType;
};

export type TranslationResponse = IBaseRestApiResponse & {
  _id: number;
  analysis:
    | { error: string }
    | {
        translated_payload: Record<TranslationFields, string> & {
          images?: Record<TranslationImageField, string>;
        };
        body_html: "";
        payload: Record<TranslationFields, string> & {
          images?: Record<TranslationImageField, string>;
        };
        target_language: string;
        source_language: string;
        translation_type: TranslationType;
      };
};
