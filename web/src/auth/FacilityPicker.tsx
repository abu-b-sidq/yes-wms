import React from 'react';
import { useAuth } from './AuthContext';
import AssistantAvatar from '../components/chat/AssistantAvatar';
import { ASSISTANT_NAME } from '../constants/branding';

export default function FacilityPicker() {
  const { facilities, chooseFacility, facilityLoading, signOut } = useAuth();

  return (
    <div className="h-[100dvh] overflow-hidden px-3 py-3 md:px-4">
      <div className="mx-auto grid h-full max-w-6xl gap-4 lg:grid-cols-[0.95fr_1.05fr]">
        <section className="soft-panel flex flex-col justify-between gap-6 overflow-hidden px-6 py-7 md:px-7 md:py-8">
          <div className="space-y-4">
            <p className="ops-label text-xs">
              Facility Setup
            </p>
            <h1 className="max-w-xl text-3xl font-semibold leading-tight text-[var(--ops-text)] md:text-4xl">
              Choose the warehouse you want {ASSISTANT_NAME} to follow.
            </h1>
            <p className="max-w-lg text-sm leading-6 text-[var(--ops-text-muted)]">
              Each facility changes the live notifications, conversation context, and warehouse
              metrics available inside YES WMS.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-[180px_1fr] md:items-end">
            <AssistantAvatar size="md" className="mx-auto md:mx-0" />
            <div className="ops-note-card rounded-[24px] p-4">
              <p className="ops-label text-xs text-[var(--ops-highlight)]">
                {ASSISTANT_NAME}
              </p>
              <p className="mt-2 text-sm leading-6 text-[var(--ops-text-muted)]">
                Pick the facility you want me to speak for, and I'll tailor prompts, alerts, and
                summaries to that warehouse only.
              </p>
            </div>
          </div>
        </section>

        <section className="soft-panel flex min-h-0 flex-col overflow-hidden px-5 py-6 md:px-7">
          <div className="mb-5 space-y-2">
            <p className="ops-label text-xs">
              Available Facilities
            </p>
            <h2 className="text-2xl font-semibold text-[var(--ops-text)] md:text-3xl">Select your workspace</h2>
          </div>

          <div className="min-h-0 space-y-3 overflow-y-auto pr-1">
            {facilities.map((facility) => (
              <button
                key={facility.code}
                onClick={() => chooseFacility(facility)}
                disabled={facilityLoading}
                className="ops-card-soft group w-full rounded-[22px] px-4 py-4 text-left transition hover:-translate-y-0.5 hover:border-[var(--ops-border-strong)] hover:bg-[rgba(255,255,255,0.06)] disabled:cursor-not-allowed disabled:opacity-50"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="text-base font-semibold text-[var(--ops-text)] group-hover:text-[var(--ops-highlight)]">
                      {facility.name}
                    </div>
                    <div className="mt-1 text-sm text-[var(--ops-text-muted)]">Code: {facility.code}</div>
                  </div>
                  <div className="ops-chip-highlight rounded-full px-3 py-1 text-xs font-medium">
                    Open
                  </div>
                </div>
              </button>
            ))}
          </div>

          <button
            onClick={signOut}
            className="mt-6 text-sm font-medium text-[var(--ops-text-muted)] transition hover:text-[var(--ops-text)]"
          >
            Sign out
          </button>
        </section>
      </div>
    </div>
  );
}
