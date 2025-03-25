import { useFormikContext } from "formik";
import { debounce } from "lodash";
import * as React from "react";
import { IArticle } from "superdesk-api";
import { Option, ResizablePanels, Spacer } from "superdesk-ui-framework/react";
import { FormTextEditorInput, FormTextInput, Select } from "../../../components";
import { FORM_ID, SUBMITTER_ID, TRANSLATION_VERSIONS } from "../../../constants";
import { useSuperdesk } from "../../../context";
import { getObjectEntries } from "../../../utilities";
import {
  FORM_FIELDS,
  getTranslationFormValues,
  getWritethrus,
  isTranslationVersion,
  TranslationForm as TranslationFormType,
  TranslationEntry,
} from "../helpers";
import { TranslationSettings } from "../settings";
import { ToolTabs } from "../tool-tabs";

const Entry = ({
  initialVersion,
}: {
  initialVersion: keyof TranslationEntry;
}) => {
  const superdesk = useSuperdesk(),
    { gettext } = superdesk.localization,
    { GenericFormFieldType } = superdesk.forms,
    { values, isValid } = useFormikContext<TranslationFormType>(),
    [version, setVersion] =
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
            {value.getLabel(superdesk)}
          </Option>
        ))}
      </Select>
      {getObjectEntries(FORM_FIELDS).map(([key, value]) => {
        const name = value.getName(values.writethru, version);
        const schema = superdesk.instance.config.schema?.["Story"]?.[key];
        const sharedProps = {
          key: name,
          name,
          label: value.getLabel(superdesk),
          ...(version === TRANSLATION_VERSIONS.manualTranslation.value && {
            maxLength: schema?.maxlength,
          }),
        };

        switch (value.getType(superdesk)) {
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

const useTranslationPanelsHeight = (
  containerRef: React.RefObject<HTMLDivElement>
) => {
  const [panelHeight, setPanelHeight] = React.useState<number | null>(null);

  React.useEffect(() => {
    if (!containerRef.current) return;

    const parent = containerRef.current.parentElement,
      grandparent = parent?.parentElement;
    if (!parent || !grandparent) return;

    const calculateHeight = () => {
        const grandparentStyles = getComputedStyle(grandparent),
          grandparentPaddingTop = parseFloat(grandparentStyles.paddingTop) ?? 0,
          grandparentPaddingBottom =
            parseFloat(grandparentStyles.paddingBottom) ?? 0,
          parentStyles = getComputedStyle(parent),
          parentGap = parseFloat(parentStyles.columnGap) ?? 0,
          containerOffsetHeight =
            grandparent.offsetHeight -
            grandparentPaddingTop -
            grandparentPaddingBottom;

        const siblings = Array.from(parent.children).slice(0, -1);
        const siblingsOffsetHeight = siblings.reduce(
          (a, s) =>
            s instanceof HTMLElement ? a + s.offsetHeight + parentGap : a,
          0
        );
        if (containerOffsetHeight < siblingsOffsetHeight) return;

        setPanelHeight(containerOffsetHeight - siblingsOffsetHeight);
      },
      debouncedCalculateHeight = debounce(calculateHeight, 25);

    calculateHeight();

    const resizeObserver = new ResizeObserver(() => {
      debouncedCalculateHeight();
    });
    resizeObserver.observe(parent);

    return () => {
      resizeObserver.disconnect();
      debouncedCalculateHeight.cancel?.();
    };
  }, []);

  return panelHeight;
};

const TranslationPanels = () => {
  const containerRef = React.useRef<HTMLDivElement>(null),
    panelsHeight = useTranslationPanelsHeight(containerRef);

  return (
    <div
      ref={containerRef}
      style={{ ...(panelsHeight && { height: `${panelsHeight}px` }) }}
    >
      <ResizablePanels
        direction="horizontal"
        primarySize={{ min: 33, default: 50 }}
        secondarySize={{ min: 33, default: 50 }}
      >
        <Spacer
          h
          gap="16"
          noWrap
          style={{
            flexWrap: "wrap",
            alignContent: "start",
            paddingRight: "1rem",
            overflowY: "scroll",
            ...(panelsHeight && { height: `${panelsHeight}px` }),
          }}
        >
          <></>
          <Entry initialVersion={TRANSLATION_VERSIONS.original.value} />
        </Spacer>
        <Spacer
          h
          gap="16"
          noWrap
          style={{
            flexWrap: "wrap",
            alignContent: "start",
            padding: "0 1rem",
            overflowY: "scroll",
            ...(panelsHeight && { height: `${panelsHeight}px` }),
          }}
        >
          <></>
          <Entry initialVersion={TRANSLATION_VERSIONS.aiTranslation.value} />
        </Spacer>
      </ResizablePanels>
    </div>
  );
};

export const TranslationForm = React.forwardRef<
  HTMLFormElement,
  { article: IArticle }
>(({ article }, ref) => {
  const superdesk = useSuperdesk(),
    { resetForm, handleSubmit, status, setStatus } = useFormikContext();

  React.useEffect(() => {
    getWritethrus(article, superdesk)
      .then(({ _items }) => {
        resetForm({
          values: getTranslationFormValues(article, _items, superdesk),
        });
      })
      .catch((err) => {
        console.error({ err });
      })
      .finally(() => {
        setStatus({ ...status, isLoading: false });
      });
  }, []);

  return (
    <form
      id={FORM_ID}
      ref={ref}
      style={{ height: "100%" }}
      onSubmit={(event) => {
        event.preventDefault();
        event.stopPropagation();

        const nativeEvent = event.nativeEvent;
        if (!(nativeEvent instanceof SubmitEvent)) return;

        const submitter = nativeEvent.submitter;
        if (!submitter || submitter.id !== SUBMITTER_ID) return;

        handleSubmit(event);
      }}
    >
      <Spacer v gap="16" noWrap>
        <TranslationSettings />
        <ToolTabs />
        <TranslationPanels />
      </Spacer>
    </form>
  );
});
