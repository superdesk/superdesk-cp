import { FormikProps, useFormikContext } from "formik";
import * as React from "react";
import { Button, Option, Spacer } from "superdesk-ui-framework/react";
import { ErrorDialog, FormSelect } from "../../../components";
import {
  TRANSLATION_LANGUAGES,
  TRANSLATION_TYPES,
  WRITEABLE_TRANSLATION_VERSIONS,
} from "../../../constants";
import { useConfirm } from "../../../context";
import { typedSetFieldValue } from "../../../formik-utilties";
import { superdesk } from "../../../superdesk";
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

const getTranslation = (payload: TranslationPayload) =>
  superdesk.httpRequestJsonLocal<TranslationResponse>({
    method: "POST",
    path: "/ai",
    payload: { service: "translate", item: payload },
  });

const getPayload = (values: FormikProps<TranslationForm>["values"]) => {
  const payload = getObjectEntries(FORM_FIELDS).reduce<
    Omit<FormInputProps, "images">
  >(
    (payload, [key, value]) => {
      payload[key] = value?.mapApiValue
        ? value.mapApiValue(values.translations[values.writethru].original[key])
        : values.translations[values.writethru].original[key];
      return payload;
    },
    { headline: "", headline_extended: "", body_html: "" }
  );

  return {
    body_html: "",
    payload,
    target_language: values.translateTo,
    source_language: values.translateFrom,
    translation_type: values.translationType,
  } as const;
};

const WritethruSelect = () => {
  const { gettext } = superdesk.localization;
  const { values } = useFormikContext<TranslationForm>();

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
  const { gettext } = superdesk.localization;
  const { confirm } = useConfirm();
  const {
    values,
    setFieldValue: formikSetFieldValue,
    getFieldMeta,
    initialValues,
    status,
  } = useFormikContext<TranslationForm>();
  const setFieldValue =
    typedSetFieldValue<TranslationForm>(formikSetFieldValue);

  const clearTranslation = () => {
    for (const version of WRITEABLE_TRANSLATION_VERSIONS) {
      for (const [key, value] of getObjectEntries(FORM_FIELDS)) {
        initialValues.translations[values.writethru][version.value][key] =
          value.initialValue;
        setFieldValue(
          `translations.${values.writethru}.${version.value}.${key}`,
          value.initialValue
        );
      }
    }
  };

  const handleClearOnClick = () => {
    if (!isManualTranslationDirty({ values, getFieldMeta }))
      return clearTranslation();
    return void confirm({
      header: gettext("Confirm clear Translation"),
      body: gettext(
        "Are you sure you wish to clear and lose all changes made to this translation?"
      ),
      footerProps: {
        confirm: { buttonProps: { text: gettext("Yes, Clear") } },
        cancel: { buttonProps: { text: gettext("No") } },
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
  const { gettext } = superdesk.localization;
  const { showModal } = superdesk.ui;
  const { confirm } = useConfirm();
  const {
    values,
    setFieldValue: formikSetFieldValue,
    getFieldMeta,
    initialValues,
    status,
    setStatus,
  } = useFormikContext<TranslationForm>();
  const setFieldValue =
    typedSetFieldValue<TranslationForm>(formikSetFieldValue);

  const translateArticle = () => {
    setStatus({ ...status, isLoading: true });
    getTranslation(getPayload(values))
      .then((res) => {
        if ("error" in res.analysis) throw new Error(res.analysis.error);

        for (const version of WRITEABLE_TRANSLATION_VERSIONS) {
          for (const [key, value] of getObjectEntries(FORM_FIELDS)) {
            const translatedValue =
              res.analysis.translated_payload?.[key] ?? "";
            const fieldValue = value?.setFormValue
              ? value.setFormValue(translatedValue)
              : translatedValue;

            initialValues.translations[values.writethru][version.value][key] =
              fieldValue;
            setFieldValue(
              `translations.${values.writethru}.${version.value}.${key}`,
              fieldValue
            );
          }
        }

        if (status.isPristine) setStatus({ ...status, isPristine: false });
      })
      .catch(() => {
        showModal(({ closeModal }) => (
          <ErrorDialog message={gettext("Failed to translate writethru.")} closeModal={closeModal} />
        ));
      })
      .finally(() => {
        setStatus({ ...status, isLoading: false });
      });
  };

  const handleTranslateOnClick = () => {
    if (!isManualTranslationDirty({ values, getFieldMeta }))
      return translateArticle();
    return void confirm({
      header: gettext("Confirm Translate"),
      body: gettext(
        'By clicking "Translate" again, changes to the current manual translation will be lost. Are you sure you wish to proceed?'
      ),
      footerProps: {
        confirm: { buttonProps: { text: gettext("Yes") } },
        cancel: { buttonProps: { text: gettext("No") } },
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
      <TranslateButton />
      <ClearTranslationButton />
    </Spacer>
  );
};
