import { FormikProps, useFormikContext } from "formik";
import * as React from "react";
import { Button } from "superdesk-ui-framework/react";
import { ErrorDialog } from "../../../components";
import { WRITEABLE_TRANSLATION_VERSIONS } from "../../../constants";
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
    ...(values.glossary ? { glossary_id: values.glossary } : {}),
    ...(values.style ? { style_id: values.style } : {}),
  } as const;
};

export const TranslateButton = () => {
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
          <ErrorDialog
            message={gettext("Failed to translate writethru.")}
            closeModal={closeModal}
          />
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
