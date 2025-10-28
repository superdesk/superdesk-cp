import * as React from "react";
import { ResizablePanels, Spacer } from "superdesk-ui-framework/react";
import { TRANSLATION_VERSIONS } from "../../../constants";
import { Entry } from "./entry";
import { useTranslationPanelsHeight } from "./helpers";

export const TranslationPanels = () => {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const panelsHeight = useTranslationPanelsHeight(containerRef);

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
