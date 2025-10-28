import { debounce } from "lodash";
import * as React from "react";

/**
 * Calculates available height in the modal for the translation panels
 * based on modal and sibiling heights and paddings
 *
 * The form has multiple elements that expand to fill available vertical space
 * This hook is needed to calculate available space for the translation panels forms
 * otherwise it will not grow to fill space
 */

export const useTranslationPanelsHeight = (
  containerRef: React.RefObject<HTMLDivElement>
) => {
  const [panelHeight, setPanelHeight] = React.useState<number | null>(null);

  React.useEffect(() => {
    if (!containerRef.current) return;

    const parent = containerRef.current.parentElement;
    const grandparent = parent?.parentElement;
    if (!parent || !grandparent) return;

    const calculateHeight = () => {
        const grandparentStyles = getComputedStyle(grandparent);
        const grandparentPaddingTop =
          parseFloat(grandparentStyles.paddingTop) ?? 0;
        const grandparentPaddingBottom =
          parseFloat(grandparentStyles.paddingBottom) ?? 0;
        const parentStyles = getComputedStyle(parent);
        const parentGap = parseFloat(parentStyles.columnGap) ?? 0;
        const containerOffsetHeight =
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
