import * as React from "react";
import {
  Spacer,
  ToggleBox as SuperdeskToggleBox,
  TabContent,
  TabLabel,
  TabPanel,
  Tabs,
} from "superdesk-ui-framework/react";
import { CustomHeaderToggleBox } from "superdesk-ui-framework/react/components/ToggleBox/CustomHeaderToggleBox";
import { superdesk } from "../../../superdesk";
import { Compare } from "../compare";
import { ReplaceAll } from "../replace-all";

const useTools = () => {
  const { gettext } = superdesk.localization;

  return React.useMemo(
    () =>
      [
        { label: gettext("Compare"), component: Compare },
        { label: gettext("Replace All"), component: ReplaceAll },
      ] as const,
    [gettext]
  );
};

const useTabs = (tools: ReturnType<typeof useTools>) =>
  React.useMemo(
    () =>
      tools.reduce<{
        tabLabels: Array<React.ReactNode>;
        tabPanels: Array<React.ReactNode>;
      }>(
        (acc, { label, component: Component }, i) => {
          acc.tabLabels.push(
            <TabLabel key={`tab-label-${label}`} label={label} indexValue={i} />
          );
          acc.tabPanels.push(
            <TabPanel key={`tab-panel-${label}`} indexValue={i}>
              <Component />
            </TabPanel>
          );
          return acc;
        },
        {
          tabLabels: [],
          tabPanels: [],
        }
      ),
    [tools]
  );

const ToggleBox = () => {
  const { gettext } = superdesk.localization;
  const [tab, setTab] = React.useState(0);
  const tools = useTools();
  const toggleBoxRef = React.useRef<CustomHeaderToggleBox>(null);
  const { tabLabels, tabPanels } = useTabs(tools);

  const handleTabOnClick = (newTab: number): void => {
    if (tab === newTab) return void toggleBoxRef.current?.toggle();
    setTab(newTab);
    if (!toggleBoxRef.current?.isOpen()) toggleBoxRef.current?.toggle();
  };

  const getToggleButtonLabel = (isOpen: boolean) => {
    const params = { tool: tools[tab].label };

    return isOpen
      ? gettext("Hide {{tool}}", params)
      : gettext("Show {{tool}}", params);
  };

  return (
    <SuperdeskToggleBox
      variant="custom-header"
      header={<Tabs onClick={handleTabOnClick}>{tabLabels}</Tabs>}
      getToggleButtonLabel={getToggleButtonLabel}
      toggleBoxRef={toggleBoxRef}
    >
      <TabContent activePanel={tab}>{tabPanels}</TabContent>
    </SuperdeskToggleBox>
  );
};

export const ToolTabs = () => (
  <Spacer v gap="0" alignItems="stretch" noWrap>
    <></>
    <ToggleBox />
  </Spacer>
);
