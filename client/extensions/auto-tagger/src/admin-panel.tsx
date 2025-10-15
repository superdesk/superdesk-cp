import * as React from "react";
import { ISuperdesk } from "superdesk-api";
import { Button, Input, ToggleBox } from "superdesk-ui-framework/react";

type APIItem = {
  _id: string;
  _etag: string;
  key: string;
  value: string;
};

const API_KEY_ID = "semaphore_api_key";

export const AdminPanel = ({ superdesk }: { superdesk: ISuperdesk }) => {
  const { gettext } = superdesk.localization;
  const { getCurrentUser } = superdesk.session;
  const { httpRequestJsonLocal } = superdesk;

  const [isAdmin, setIsAdmin] = React.useState(false);
  const [isLoading, setIsLoading] = React.useState(true);
  const [apiKey, setApiKey] = React.useState("");
  const apiItem = React.useRef<APIItem>();

  React.useEffect(() => {
    getCurrentUser().then((user) => {
      setIsAdmin(user.user_type === "administrator");
    });
  }, []);

  React.useEffect(() => {
    if (!isAdmin) return;
    httpRequestJsonLocal<{ _items: Array<APIItem> }>({
      method: "GET",
      path: "/app_config",
    })
      .then(({ _items }) => {
        const found = _items.find((i) => i.key === API_KEY_ID);
        if (!found) return;
        apiItem.current = found;
        setApiKey(found.value);
      })
      .catch(() => {})
      .finally(() => {
        setIsLoading(false);
      });
  }, [isAdmin]);

  const sendApiRequest = React.useCallback(() => {
    if (!apiItem.current)
      return httpRequestJsonLocal<APIItem>({
        method: "POST",
        path: "/app_config",
        payload: { key: API_KEY_ID, value: apiKey },
      });
    return httpRequestJsonLocal<APIItem>({
      method: "PATCH",
      path: `/app_config/${apiItem.current._id}`,
      payload: { value: apiKey },
      headers: {
        "If-Match": apiItem.current._etag,
      },
    });
  }, [apiKey, apiItem.current]);

  const updateApiKey = () => {
    setIsLoading(true);
    sendApiRequest()
      .then((item) => {
        apiItem.current = item;
        setApiKey(item.value);
      })
      .catch(() => {})
      .finally(() => {
        setIsLoading(false);
      });
  };

  if (!isAdmin) return null;
  return (
    <ToggleBox variant="simple" title={gettext("Administrator")}>
      <div className="auto-tagger__admin-panel-container">
        <Input
          type="text"
          value={apiKey}
          onChange={setApiKey}
          label={gettext("API Key")}
        />
        <Button
          text={gettext("Save")}
          onClick={updateApiKey}
          disabled={isLoading || !apiKey}
          isLoading={isLoading}
        />
      </div>
    </ToggleBox>
  );
};
