import * as React from "react";
import { Option, Spacer } from "superdesk-ui-framework/react";
import { FormSelect } from "../../../components";
import { TRANSLATION_LANGUAGES, TRANSLATION_TYPES } from "../../../constants";
import { superdesk } from "../../../superdesk";
import { getObjectEntries } from "../../../utilities";
import { TranslationForm } from "../helpers";
import { ClearTranslationButton } from "./clear-translation-button";
import { GlossarySelect } from "./glossary-select";
import { StyleSelect } from "./style-select";
import { TranslateButton } from "./translate-button";
import { WritethruSelect } from "./writethru-select";

export const TranslationSettings = () => {
  const { gettext } = superdesk.localization;

  return (
    <Spacer h gap="16" alignItems="end" noWrap>
      <WritethruSelect />
      <FormSelect<TranslationForm>
        name="translationType"
        label={gettext("Translation Engine")}
      >
        {getObjectEntries(TRANSLATION_TYPES).map(([value, label]) => (
          <Option value={value} key={`translationType-${value}`}>
            {label}
          </Option>
        ))}
      </FormSelect>
      <FormSelect<TranslationForm>
        name="translateFrom"
        label={gettext("Translate From")}
      >
        {getObjectEntries(TRANSLATION_LANGUAGES).map(([key, value]) => (
          <Option value={value.value} key={`translateFrom-${key}`}>
            {value.label}
          </Option>
        ))}
      </FormSelect>
      <FormSelect<TranslationForm>
        name="translateTo"
        label={gettext("Translate To")}
      >
        {getObjectEntries(TRANSLATION_LANGUAGES).map(([key, value]) => (
          <Option value={value.value} key={`translateTo-${key}`}>
            {value.label}
          </Option>
        ))}
      </FormSelect>
      <GlossarySelect />
      <StyleSelect />
      <TranslateButton />
      <ClearTranslationButton />
    </Spacer>
  );
};
