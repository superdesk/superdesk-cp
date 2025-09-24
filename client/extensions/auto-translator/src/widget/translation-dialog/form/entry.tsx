import { useFormikContext } from "formik";
import * as React from "react";
import { Option } from "superdesk-ui-framework/react";
import {
  FormTextEditorInput,
  FormTextInput,
  Select,
} from "../../../components";
import { TRANSLATION_VERSIONS } from "../../../constants";
import { superdesk } from "../../../superdesk";
import { getObjectEntries } from "../../../utilities";
import {
  FORM_FIELDS,
  isTranslationVersion,
  TranslationEntry,
  TranslationForm as TranslationFormType,
} from "../helpers";

export const Entry = ({
  initialVersion,
}: {
  initialVersion: keyof TranslationEntry;
}) => {
  const { gettext } = superdesk.localization;
  const { GenericFormFieldType } = superdesk.forms;
  const { values, isValid } = useFormikContext<TranslationFormType>();
  const [version, setVersion] =
      React.useState<keyof TranslationEntry>(initialVersion),
    translationVersions =
      initialVersion === TRANSLATION_VERSIONS.original.value
        ? getObjectEntries(TRANSLATION_VERSIONS).filter(
            ([key]) => key !== TRANSLATION_VERSIONS.manualTranslation.value
          )
        : getObjectEntries(TRANSLATION_VERSIONS);

  return (
    <>
      <Select
        value={version}
        label={
          initialVersion === TRANSLATION_VERSIONS.original.value
            ? gettext("Version (Original Content)")
            : gettext("Version (Translated Content)")
        }
        onChange={(newValue) => {
          if (isTranslationVersion(newValue)) setVersion(newValue);
        }}
        error={
          initialVersion === TRANSLATION_VERSIONS.aiTranslation.value &&
          !isValid &&
          version !== TRANSLATION_VERSIONS.manualTranslation.value
            ? gettext("Fix Manual Translation errors to apply translation")
            : undefined
        }
      >
        {translationVersions.map(([key, value]) => (
          <Option value={value.value} key={`version-${key}`}>
            {value.label}
          </Option>
        ))}
      </Select>
      {getObjectEntries(FORM_FIELDS).map(([key, value]) => {
        const name = value.getName(values.writethru, version);
        const schema = superdesk.instance.config.schema?.["Story"]?.[key];
        const sharedProps = {
          key: name,
          name,
          label: value.label,
          ...(version === TRANSLATION_VERSIONS.manualTranslation.value && {
            maxLength: schema?.maxlength,
          }),
        };

        switch (value.type) {
          case GenericFormFieldType.textEditor3:
            return (
              <FormTextEditorInput<TranslationFormType>
                {...sharedProps}
                readOnly={
                  version !== TRANSLATION_VERSIONS.manualTranslation.value
                }
                maxLength={
                  version !== TRANSLATION_VERSIONS.manualTranslation.value
                    ? undefined
                    : Number.MAX_SAFE_INTEGER
                }
              />
            );
          default:
            return (
              <FormTextInput<TranslationFormType>
                {...sharedProps}
                readonly={
                  version !== TRANSLATION_VERSIONS.manualTranslation.value
                }
              />
            );
        }
      })}
    </>
  );
};
