import {
  TRANSLATION_LANGUAGES_CODES_MAP,
  TRANSLATION_VERSIONS,
} from "../../constants";
import {
  TranslationFields,
  TranslationImageField,
  TranslationType,
} from "../../typings/translation";

export type FormInputProps = Record<TranslationFields, string> & {
  images: Record<TranslationImageField, { description: string; href: string }>;
};

export type TranslationEntry = Record<
  keyof typeof TRANSLATION_VERSIONS,
  FormInputProps
>;

export type TranslationDialogFormProps = {
  writethru: string;
  translationType: TranslationType;
  translateFrom: (typeof TRANSLATION_LANGUAGES_CODES_MAP)[keyof typeof TRANSLATION_LANGUAGES_CODES_MAP];
  translateTo: (typeof TRANSLATION_LANGUAGES_CODES_MAP)[keyof typeof TRANSLATION_LANGUAGES_CODES_MAP];
  translations: Record<string, TranslationEntry>;
};
