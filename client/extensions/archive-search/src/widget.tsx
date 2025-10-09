import * as React from "react";
import { ISearchPanelWidgetProps, IVocabularyItem } from "superdesk-api";
import {
  Input,
  Spacer,
  SpacerBlock,
  MultiSelect as SuperdeskMultiSelect,
  DatePickerISO
} from "superdesk-ui-framework/react";
import { superdesk } from "./superdesk";

const { gettext } = superdesk.localization;
const { getVocabulary, getVocabularyItemNameTranslated } =
  superdesk.entities.vocabulary;
const { view, default_language } = superdesk.instance.config;
const { dateformat } = view;
const { getLocaleForDatePicker } = superdesk.ui.framework;

interface IParams {
  from: string;
  to: string;
  slugline: string;
  headline: string;
  story_text: string;
  byline: string;
  distribution: string[];
  categories: string[];
  languages: string[];
  source: string[];
}

type MultiSelectProps = Record<
  string,
  {
    vocabularyKey: string;
    label: string;
    onChange: (
      setParams: (params: Partial<IParams>) => void
    ) => (selected: IVocabularyItem[]) => void;
  }
>;

const HEADER_BUTTON_BAR_PROPS = [
  { label: gettext("Today"), days: 1 },
  { label: gettext("Tomorrow"), days: 2 },
  { label: gettext("In 2 days"), days: 3 },
];

const multiSelects: MultiSelectProps = {
  distribution: {
    vocabularyKey: "distribution",
    label: gettext("Services"),
    onChange: (setParams) => (selected) => {
      setParams({ distribution: selected.map((s) => s.qcode) });
    },
  },
  categories: {
    vocabularyKey: "categories",
    label: gettext("Wire"),
    onChange: (setParams) => (selected) => {
      setParams({ categories: selected.map((s) => s.qcode) });
    },
  },
  languages: {
    vocabularyKey: "languages",
    label: gettext("Languages"),
    onChange: (setParams) => (selected) => {
      setParams({ languages: selected.map((s) => s.qcode) });
    },
  },
  source: {
    vocabularyKey: "source",
    label: gettext("Info source"),
    onChange: (setParams) => (selected) => {
      setParams({ source: selected.map((s) => s.qcode) });
    },
  },
};

const MultiSelect = ({
  vocabularyKey,
  label,
  value,
  onChange,
}: Omit<MultiSelectProps[string], "onChange"> & {
  value: string[];
  onChange: (selected: IVocabularyItem[]) => void;
}) => {
  const options = React.useMemo(
    () => getVocabulary(vocabularyKey)?.items ?? [],
    [vocabularyKey]
  );

  return (
    <SuperdeskMultiSelect<IVocabularyItem>
      filter
      showSelectAll
      label={label}
      value={options.filter((o) => (value ?? []).includes(o.qcode))}
      options={options}
      optionLabel={getVocabularyItemNameTranslated}
      onChange={onChange}
    />
  );
};

export class SearchPanelWidget extends React.PureComponent<
  ISearchPanelWidgetProps<IParams>
> {
  render() {
    const { provider, params, setParams } = this.props;

    if (provider !== "archive_search") return null;
    return (
      <fieldset>
        <Spacer v gap="16">
          <DatePickerISO
            label={gettext("From")}
            value={params.from ?? ""}
            dateFormat={dateformat}
            locale={{
              type: "full",
              payload: getLocaleForDatePicker(default_language),
            }}
            onChange={(v) => {
              setParams({ from: v });
            }}
            headerButtonBar={HEADER_BUTTON_BAR_PROPS}
            showNavigators
          />
          <DatePickerISO
            label={gettext("To")}
            value={params.to ?? ""}
            dateFormat={dateformat}
            locale={{
              type: "full",
              payload: getLocaleForDatePicker(default_language),
            }}
            onChange={(v) => {
              setParams({ to: v });
            }}
            headerButtonBar={HEADER_BUTTON_BAR_PROPS}
            showNavigators
          />
          <Spacer h gap="16">
            <Input
              label={gettext("Slugline")}
              value={params.slugline || ""}
              type="text"
              onChange={(value) => {
                setParams({ slugline: value });
              }}
            />
            <Input
              label={gettext("Headline")}
              value={params.headline || ""}
              type="text"
              onChange={(value) => {
                setParams({ headline: value });
              }}
            />
          </Spacer>
          <Input
            label={gettext("Story Text")}
            value={params.story_text || ""}
            type="text"
            onChange={(value) => {
              setParams({ story_text: value });
            }}
          />
          <Input
            label={gettext("Byline")}
            value={params.byline || ""}
            type="text"
            onChange={(value) => {
              setParams({ byline: value });
            }}
          />
          {Object.values(multiSelects).map(
            ({ vocabularyKey, label, onChange }, i) => (
              <React.Fragment key={vocabularyKey}>
                {i !== 0 && <SpacerBlock v gap="16" />}
                <MultiSelect
                  vocabularyKey={vocabularyKey}
                  label={label}
                  value={
                    params[vocabularyKey as keyof typeof params] as string[]
                  }
                  onChange={onChange(setParams)}
                />
              </React.Fragment>
            )
          )}
        </Spacer>
      </fieldset>
    );
  }
}
