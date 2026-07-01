import { useCallback, useRef, useState } from "react";
import type { ApiClient, ConsentScope } from "@looma/shared-core";
import { ensureConsent as ensureConsentApi } from "@looma/shared-core";
import ConsentModal from "../brand/components/ConsentModal";

interface PendingConsent {
  scope: ConsentScope;
  resolve: (granted: boolean) => void;
}

export function useConsent(getClient: () => ApiClient) {
  const [pending, setPending] = useState<PendingConsent | null>(null);
  const cacheRef = useRef<Partial<Record<ConsentScope, boolean>>>({});

  const promptUser = useCallback((scope: ConsentScope) => {
    return new Promise<boolean>((resolve) => {
      setPending({ scope, resolve });
    });
  }, []);

  const ensureConsent = useCallback(
    async (scope: ConsentScope): Promise<boolean> => {
      if (cacheRef.current[scope]) return true;
      const ok = await ensureConsentApi(getClient(), scope, promptUser);
      if (ok) cacheRef.current[scope] = true;
      return ok;
    },
    [getClient, promptUser],
  );

  const handleAccept = useCallback(() => {
    pending?.resolve(true);
    setPending(null);
  }, [pending]);

  const handleDecline = useCallback(() => {
    pending?.resolve(false);
    setPending(null);
  }, [pending]);

  const consentPrompt = pending ? (
    <ConsentModal scope={pending.scope} onAccept={handleAccept} onDecline={handleDecline} />
  ) : null;

  return { ensureConsent, consentPrompt };
}
