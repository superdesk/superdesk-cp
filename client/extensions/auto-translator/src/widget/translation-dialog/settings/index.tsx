import { FormikProps, useFormikContext } from "formik";
import * as React from "react";
import { ISuperdesk } from "superdesk-api";
import { Button, Option, Spacer } from "superdesk-ui-framework/react";
import { FormSelect } from "../../../components";
import {
  TRANSLATION_LANGUAGES,
  TRANSLATION_TYPES,
  TRANSLATION_VERSIONS,
} from "../../../constants";
import { useConfirm, useSuperdesk } from "../../../context";
import { typedSetFieldValue } from "../../../formik-utilties";
import {
  TranslationPayload,
  TranslationResponse,
} from "../../../typings/translation";
import { getObjectEntries } from "../../../utilities";
import {
  FORM_FIELDS,
  FormInputProps,
  isManualTranslationDirty,
  TranslationForm,
} from "../helpers";

const getTranslation = (
  payload: TranslationPayload,
  { httpRequestJsonLocal }: ISuperdesk
) =>
  httpRequestJsonLocal<TranslationResponse>({
    method: "POST",
    path: "/ai",
    payload: { service: "translate", item: payload },
  });

const getPayload = (values: FormikProps<TranslationForm>["values"]) =>
  ({
    body_html: "",
    payload: getObjectEntries(FORM_FIELDS).reduce<
      Omit<FormInputProps, "images">
    >(
      (payload, [key, value]) => {
        payload[key] = value?.mapApiValue
          ? value.mapApiValue(
              values.translations[values.writethru].original[key]
            )
          : values.translations[values.writethru].original[key];
        return payload;
      },
      { headline: "", headline_extended: "", body_html: "" }
    ),
    target_language: values.translateTo,
    source_language: values.translateFrom,
    translation_type: values.translationType,
  } as const);

const WritethruSelect = () => {
  const superdesk = useSuperdesk(),
    { gettext } = superdesk.localization,
    { values } = useFormikContext<TranslationForm>();

  return (
    <FormSelect<TranslationForm> name="writethru" label={gettext("Writethru")}>
      <Option value="current">{values.translations.current.label}</Option>
      {getObjectEntries(values.translations)
        .filter(([k]) => k !== "current")
        .map(([k, v]) => (
          <Option value={k} key={`writethru-${k}`}>
            {v.label}
          </Option>
        ))}
    </FormSelect>
  );
};

const ClearTranslationButton = () => {
  const superdesk = useSuperdesk(),
    { gettext } = superdesk.localization;
  const { confirm } = useConfirm(),
    {
      values,
      setFieldValue: formikSetFieldValue,
      getFieldMeta,
      initialValues,
      status,
    } = useFormikContext<TranslationForm>(),
    setFieldValue = typedSetFieldValue<TranslationForm>(formikSetFieldValue);

  const clearTranslation = () => {
    const versions = [
      TRANSLATION_VERSIONS.aiTranslation.value,
      TRANSLATION_VERSIONS.manualTranslation.value,
    ] as const;

    for (const version of versions) {
      for (const [key, value] of getObjectEntries(FORM_FIELDS)) {
        initialValues.translations[values.writethru][version][key] =
          value.initialValue;
        setFieldValue(
          `translations.${values.writethru}.${version}.${key}`,
          value.initialValue
        );
      }
    }
  };

  const handleClearOnClick = () => {
    if (!isManualTranslationDirty({ values, getFieldMeta }, superdesk))
      return clearTranslation();
    return void confirm({
      header: gettext("Confirm clear Translation"),
      body: gettext(
        "Are you sure you wish to clear and lose all changes made to this translation?"
      ),
      footerProps: {
        confirm: { text: gettext("Yes, Clear") },
        cancel: { text: gettext("No") },
      },
    }).then((confirmed) => {
      if (confirmed) clearTranslation();
    });
  };

  return (
    <Button
      text={gettext("Clear")}
      style="hollow"
      disabled={status.isLoading}
      onClick={handleClearOnClick}
    />
  );
};

const TranslateButton = () => {
  const superdesk = useSuperdesk(),
    { gettext } = superdesk.localization;
  const { confirm } = useConfirm(),
    {
      values,
      setFieldValue: formikSetFieldValue,
      getFieldMeta,
      initialValues,
      status,
      setStatus,
    } = useFormikContext<TranslationForm>(),
    setFieldValue = typedSetFieldValue<TranslationForm>(formikSetFieldValue);

  const translateArticle = () => {
    setStatus({ ...status, isLoading: true });
    getTranslation(getPayload(values), superdesk)
      .then((res) => {
        if ("error" in res.analysis) throw new Error(res.analysis.error);

        const versions = [
          TRANSLATION_VERSIONS.aiTranslation.value,
          TRANSLATION_VERSIONS.manualTranslation.value,
        ] as const;
        for (const version of versions) {
          for (const [key, value] of getObjectEntries(FORM_FIELDS)) {
            const rValue = res.analysis.translated_payload?.[key] ?? "",
              fieldValue = value?.setFormValue
                ? value.setFormValue(rValue)
                : rValue;

            initialValues.translations[values.writethru][version][key] =
              fieldValue;
            setFieldValue(
              `translations.${values.writethru}.${version}.${key}`,
              fieldValue
            );
          }
        }

        if (status.isPristine) setStatus({ ...status, isPristine: false });
      })
      .catch((err) => {
        console.error({ err });
      })
      .finally(() => {
        setStatus({ ...status, isLoading: false });
      });
  };

  const handleTranslateOnClick = () => {
    if (!isManualTranslationDirty({ values, getFieldMeta }, superdesk))
      return translateArticle();
    return void confirm({
      header: gettext("Confirm Translate"),
      body: gettext(
        'By clicking "Translate" again, changes to the current manual translation will be lost. Are you sure you wish to proceed?'
      ),
      footerProps: {
        confirm: { text: gettext("Yes") },
        cancel: { text: gettext("No") },
      },
    }).then((confirmed) => {
      if (confirmed) translateArticle();
    });
  };

  return (
    <Button
      text={gettext("Translate")}
      type="primary"
      isLoading={status.isLoading}
      onClick={handleTranslateOnClick}
    />
  );
};

export const TranslationSettings = () => {
  const superdesk = useSuperdesk(),
    { gettext } = superdesk.localization;

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
            {value.getLabel(superdesk)}
          </Option>
        ))}
      </FormSelect>
      <FormSelect<TranslationForm>
        name="translateTo"
        label={gettext("Translate To")}
      >
        {getObjectEntries(TRANSLATION_LANGUAGES).map(([key, value]) => (
          <Option value={value.value} key={`translateTo-${key}`}>
            {value.getLabel(superdesk)}
          </Option>
        ))}
      </FormSelect>
      <TranslateButton />
      <ClearTranslationButton />
    </Spacer>
  );
};
