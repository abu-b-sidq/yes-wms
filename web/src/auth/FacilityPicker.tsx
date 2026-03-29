import React from 'react';
import { useAuth } from './AuthContext';

export default function FacilityPicker() {
  const { facilities, chooseFacility, facilityLoading, signOut } = useAuth();

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-lg p-8">
          <div className="text-center mb-6">
            <h1 className="text-2xl font-bold text-gray-900">Select Facility</h1>
            <p className="text-gray-500 mt-1">Choose a warehouse to work with</p>
          </div>

          <div className="space-y-3">
            {facilities.map((facility) => (
              <button
                key={facility.code}
                onClick={() => chooseFacility(facility)}
                disabled={facilityLoading}
                className="w-full text-left px-4 py-4 border border-gray-200 rounded-xl hover:border-primary-400 hover:bg-primary-50 disabled:opacity-50 transition group"
              >
                <div className="font-semibold text-gray-900 group-hover:text-primary-700">
                  {facility.name}
                </div>
                <div className="text-sm text-gray-500 mt-0.5">
                  Code: {facility.code}
                </div>
              </button>
            ))}
          </div>

          <button
            onClick={signOut}
            className="w-full mt-6 text-gray-500 hover:text-gray-700 text-sm transition"
          >
            Sign out
          </button>
        </div>
      </div>
    </div>
  );
}
