import * as React from "react";
import { ISearchPanelWidgetProps, IVocabularyItem } from "superdesk-api";
import {
  Input,
  MultiSelect as SuperdeskMultiSelect,
} from "superdesk-ui-framework/react";
import { DatePickerISO } from "./date-picker";
import { superdesk } from "./superdesk";

const { gettext } = superdesk.localization;

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

const HEADER_BUTTON_BAR_PROPS = [
  { label: gettext("Today"), days: 1 },
  { label: gettext("Tomorrow"), days: 2 },
  { label: gettext("In 2 days"), days: 3 },
];

type MultiSelectProps = Record<
  string,
  {
    label: string;
    onChange: (
      setParams: (params: Partial<IParams>) => void
    ) => (selected: IVocabularyItem[]) => void;
  }
>;

const multiSelects: MultiSelectProps = {
  distribution: {
    label: gettext("Services"),
    onChange: (setParams) => (selected) => {
      setParams({ distribution: selected.map((s) => s.qcode) });
    },
  },
  categories: {
    label: gettext("Wire"),
    onChange: (setParams) => (selected) => {
      setParams({ categories: selected.map((s) => s.qcode) });
    },
  },
  languages: {
    label: gettext("Languages"),
    onChange: (setParams) => (selected) => {
      setParams({ languages: selected.map((s) => s.qcode) });
    },
  },
  source: {
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
}: Omit<MultiSelectProps[string], "label" | "onChange" | "defaultValue"> & {
  vocabularyKey: string;
  label: string;
  value: any;
  onChange: (selected: IVocabularyItem[]) => void;
}) => {
  const { getVocabulary } = superdesk.entities.vocabulary;

  const options = React.useMemo(
    () => getVocabulary(vocabularyKey)?.items ?? [],
    [vocabularyKey]
  );

  return (
    <div className="form__row">
      <SuperdeskMultiSelect<IVocabularyItem>
        filter
        showSelectAll
        label={label}
        value={options.filter((o) => (value ?? []).includes(o.qcode))}
        options={options}
        optionLabel={(item) => item.name}
        onChange={onChange}
      />
    </div>
  );
};

export const widgetFactory = (): React.ComponentType<
  ISearchPanelWidgetProps<IParams>
> => {
  return class SearchPanelWidget extends React.PureComponent<
    ISearchPanelWidgetProps<IParams>
  > {
    render() {
      const { provider, params, setParams } = this.props;

      if (provider !== "archive_search") return null;
      return (
        <fieldset>
          <div className="form__row">
            <DatePickerISO
              label={gettext("From")}
              value={params.from ?? ""}
              dateFormat="YYYY-MM-DD"
              onChange={(v) => {
                setParams({ from: v });
              }}
              headerButtonBar={HEADER_BUTTON_BAR_PROPS}
            />
          </div>
          <div className="form__row">
            <DatePickerISO
              label={gettext("To")}
              value={params.to ?? ""}
              dateFormat="YYYY-MM-DD"
              onChange={(v) => {
                setParams({ to: v });
              }}
              headerButtonBar={HEADER_BUTTON_BAR_PROPS}
            />
          </div>
          <div className="form__row form__row--flex gap-1">
            <div className="flex-1">
              <Input
                label={gettext("Slugline")}
                value={params.slugline || ""}
                type="text"
                tabindex={0}
                onChange={(value) => {
                  setParams({ slugline: value });
                }}
              />
            </div>
            <div className="flex-1">
              <Input
                label={gettext("Headline")}
                value={params.headline || ""}
                type="text"
                tabindex={0}
                onChange={(value) => {
                  setParams({ headline: value });
                }}
              />
            </div>
          </div>
          <div className="form__row">
            <Input
              label={gettext("Story Text")}
              value={params.story_text || ""}
              type="text"
              tabindex={0}
              onChange={(value) => {
                setParams({ story_text: value });
              }}
            />
          </div>
          <div className="form__row">
            <Input
              label={gettext("Byline")}
              value={params.byline || ""}
              type="text"
              tabindex={0}
              onChange={(value) => {
                setParams({ byline: value });
              }}
            />
          </div>
          {Object.entries(multiSelects).map(([key, { label, onChange }]) => (
            <MultiSelect
              key={key}
              vocabularyKey={key}
              label={label}
              value={params[key as keyof typeof params]}
              onChange={onChange(setParams)}
            />
          ))}
        </fieldset>
      );
    }
  };
};
