import { useFormikContext } from "formik";
import * as React from "react";
import { Button } from "superdesk-ui-framework/react";
import { WRITEABLE_TRANSLATION_VERSIONS } from "../../../constants";
import { useConfirm } from "../../../context";
import { typedSetFieldValue } from "../../../formik-utilties";
import { superdesk } from "../../../superdesk";
import { getObjectEntries } from "../../../utilities";
import {
  FORM_FIELDS,
  isManualTranslationDirty,
  TranslationForm,
} from "../helpers";

export const ClearTranslationButton = () => {
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
