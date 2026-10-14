/**
 * A small warning text explaining that the app provides AI answers, not medical advice.
 */
export function AiDisclaimer() {
  return (
    <p className="mt-6 border-t border-neutral-200 pt-4 text-xs text-neutral-500">
      This is retrieved content which may no be perfect always and should not be
      treated as medical advice. Always check with your doctor or pharmacist
      before acting on it.
    </p>
  );
}
