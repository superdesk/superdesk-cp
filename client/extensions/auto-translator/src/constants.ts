import { superdesk } from "./superdesk";

const { gettext } = superdesk.localization;

const WIDGET_ID = "auto-translator" as const;
const FORM_ID = `${WIDGET_ID}-form` as const;
const SUBMITTER_ID = `submit-${WIDGET_ID}-button` as const;

const TRANSLATION_TYPES = {
  basic: "Google Basic",
  advanced_nmt: "Google NMT",
  // advanced_llm: "Google LLM",
  deepl: "DeepL",
} as const;

const TRANSLATION_LANGUAGES = {
  en: {
    value: "en",
    label: gettext("English"),
  },
  fr: {
    value: "fr",
    label: gettext("French"),
  },
} as const;

const TRANSLATION_VERSIONS = {
  original: {
    value: "original",
    label: gettext("Original"),
  },
  aiTranslation: {
    value: "aiTranslation",
    label: gettext("AI Translation"),
  },
  manualTranslation: {
    value: "manualTranslation",
    label: gettext("Manual Translation"),
  },
} as const;

const WRITEABLE_TRANSLATION_VERSIONS = [
  TRANSLATION_VERSIONS.aiTranslation,
  TRANSLATION_VERSIONS.manualTranslation,
] as const;

// https://www.andiamo.co.uk/resources/iso-language-codes/
const TRANSLATION_LANGUAGES_CODES_MAP = {
  en: "en",
  "en-au": "en",
  "en-bz": "en",
  "en-ca": "en",
  "en-ie": "en",
  "en-jm": "en",
  "en-nz": "en",
  "en-za": "en",
  "en-tt": "en",
  "en-gb": "en",
  "en-us": "en",
  fr: "fr",
  "fr-be": "fr",
  "fr-ca": "fr",
  "fr-lu": "fr",
  "fr-ch": "fr",
} as const;

export {
  FORM_ID,
  SUBMITTER_ID,
  TRANSLATION_LANGUAGES,
  TRANSLATION_LANGUAGES_CODES_MAP,
  TRANSLATION_TYPES,
  TRANSLATION_VERSIONS,
  WRITEABLE_TRANSLATION_VERSIONS,
  WIDGET_ID,
};
