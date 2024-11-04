const WIDGET_ID = "auto-translator-widget" as const;

const TRANSLATION_TYPES = {
  basic: "Google Basic",
  advanced_nmt: "Google NMT",
  advanced_llm: "Google LLM",
  deepl: "DeepL",
} as const;

const TRANSLATION_LANGUAGES = {
  en: "English",
  fr: "French",
} as const;

const TRANSLATION_VERSIONS = {
  original: "Original",
  aiTranslation: "AI Translation",
  manualTranslation: "Manual Translation",
} as const;

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
  WIDGET_ID,
  TRANSLATION_TYPES,
  TRANSLATION_LANGUAGES,
  TRANSLATION_VERSIONS,
  TRANSLATION_LANGUAGES_CODES_MAP,
};
