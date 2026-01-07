import { useFormikContext } from "formik";
import * as React from "react";
import { Option } from "superdesk-ui-framework/react";
import { ErrorDialog, FormSelect } from "../../../components";
import { typedSetFieldValue } from "../../../formik-utilties";
import { superdesk } from "../../../superdesk";
import { TranslationForm } from "../helpers";

type Style = {
  style_id: string;
  name: string;
  language: string;
};

export const StyleSelect = () => {
  const { gettext } = superdesk.localization;
  const { httpRequestJsonLocal } = superdesk;
  const { showModal } = superdesk.ui;
  const { values, setFieldValue: formikSetFieldValue } =
    useFormikContext<TranslationForm>();
  const setFieldValue =
    typedSetFieldValue<TranslationForm>(formikSetFieldValue);
  const [styles, setStyles] = React.useState<Array<Style>>([]);
  const filteredStyles = React.useMemo<Array<Style>>(
    () => styles.filter(({ language }) => language === values.translateTo),
    [styles, values.translateTo]
  );

  React.useEffect(() => {
    httpRequestJsonLocal<{ _items: Array<Style> }>({
      method: "GET",
      path: "/translate_config",
      urlParams: { resource: "style_rules" },
    })
      .then(({ _items }) => {
        setStyles(_items);
      })
      .catch(() => {
        showModal(({ closeModal }) => (
          <ErrorDialog
            message={gettext("Failed to get styles.")}
            closeModal={closeModal}
          />
        ));
      });
  }, []);

  React.useEffect(() => {
    const defaultStyle = filteredStyles?.[0];
    if (defaultStyle) setFieldValue("style", defaultStyle.style_id);
    else setFieldValue("style", "");
  }, [filteredStyles]);

  return (
    <FormSelect<TranslationForm> label={gettext("Style")} name={"style"}>
      <Option value="">{gettext("none")}</Option>
      {filteredStyles.map((style) => (
        <Option value={style.style_id} key={`style-${style.style_id}`}>
          {style.name}
        </Option>
      ))}
    </FormSelect>
  );
};
