import * as React from "react";
import { ISuperdesk } from "superdesk-api";

const SuperdeskContext = React.createContext<ISuperdesk | undefined>(undefined);

export const useSuperdesk = () => {
  const context = React.useContext(SuperdeskContext);
  if (!context)
    throw new Error("useSuperdesk must be used within a SuperdeskProvider");
  return context;
};

export const SuperdeskProvider = ({
  superdesk,
  children,
}: {
  superdesk: ISuperdesk;
  children: React.ReactNode;
}) => (
  <SuperdeskContext.Provider value={superdesk}>
    {children}
  </SuperdeskContext.Provider>
);
