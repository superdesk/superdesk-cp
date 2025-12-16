import { useFormikContext } from "formik";
import * as React from "react";
import { Option } from "superdesk-ui-framework/react";
import { ErrorDialog, FormSelect } from "../../../components";
import { superdesk } from "../../../superdesk";
import { TranslationForm } from "../helpers";

type Dictionary = {
  source_lang: string;
  target_lang: string;
};

type Glossary = {
  glossary_id: string;
  name: string;
  dictionaries: Array<Dictionary>;
};

export const GlossarySelect = () => {
  const { gettext } = superdesk.localization;
  const { httpRequestJsonLocal } = superdesk;
  const { showModal } = superdesk.ui;
  const { values } = useFormikContext<TranslationForm>();

  const [glossaries, setGlossaries] = React.useState<Array<Glossary>>([]);

  React.useEffect(() => {
    httpRequestJsonLocal<{ _items: Array<Glossary> }>({
      method: "GET",
      path: "/translate_config",
      urlParams: { resource: "glossaries" },
    })
      .then(({ _items }) => {
        setGlossaries(_items);
      })
      .catch(() => {
        showModal(({ closeModal }) => (
          <ErrorDialog
            message={gettext("Failed to get glossaries.")}
            closeModal={closeModal}
          />
        ));
      });
  }, []);

  return (
    <FormSelect<TranslationForm> label={gettext("Glossary")} name={"glossary"}>
      <Option value="">{gettext("none")}</Option>
      {glossaries
        .filter(({ dictionaries }) =>
          dictionaries.some(
            ({ source_lang, target_lang }) =>
              source_lang === values.translateFrom &&
              target_lang === values.translateTo
          )
        )
        .map((glossary) => (
          <Option
            value={glossary.glossary_id}
            key={`glossary-${glossary.glossary_id}`}
          >
            {glossary.name}
          </Option>
        ))}
    </FormSelect>
  );
};
