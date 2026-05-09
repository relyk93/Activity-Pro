"""
MatrixCare EHR Integration Client
===================================
MatrixCare is widely used in skilled nursing and senior living facilities,
particularly for multi-site enterprise customers.

To use in production:
1. Apply at https://www.matrixcare.com/partners/
2. Obtain api_key and facility_id from MatrixCare partner portal
3. Add to .streamlit/secrets.toml:
   [ehr]
   mc_api_key     = "your_api_key"
   mc_facility_id = "your_facility_id"
   mc_sandbox     = true

Sandbox base URL: https://api-sandbox.matrixcare.com/v1
Production base URL: https://api.matrixcare.com/v1
"""
import requests
from datetime import datetime

SANDBOX_BASE = "https://api-sandbox.matrixcare.com/v1"
PROD_BASE    = "https://api.matrixcare.com/v1"


class MatrixCareClient:
    def __init__(self, api_key: str, facility_id: str, sandbox: bool = True):
        self.api_key     = api_key
        self.facility_id = facility_id
        self.base_url    = SANDBOX_BASE if sandbox else PROD_BASE

    def _headers(self) -> dict:
        return {
            "Authorization":  f"ApiKey {self.api_key}",
            "X-Facility-Id":  self.facility_id,
            "Content-Type":   "application/json",
            "Accept":         "application/json",
        }

    def get_residents(self) -> list:
        """
        Pull resident census from MatrixCare.
        Returns list of dicts with mc_id, firstName, lastName, room, admitDate.
        """
        resp = requests.get(
            f"{self.base_url}/residents",
            headers=self._headers(),
            params={"facilityId": self.facility_id, "status": "active"},
            timeout=10
        )
        resp.raise_for_status()
        return resp.json().get("residents", [])

    def post_activity_note(self, mc_resident_id: str, activity_title: str,
                           engagement: bool, mood_before: int, mood_after: int,
                           staff_note: str, session_date: str) -> dict:
        """
        Write an activity note to a resident's MatrixCare chart.

        MatrixCare uses the /clinical/notes endpoint for documentation.
        The noteCategory "ACTIVITY" maps to the Activities section of the MDS.
        """
        mood_labels = {1:"Very Low",2:"Low",3:"Neutral",4:"Good",5:"Great"}
        engaged_text = "Engaged" if engagement else "Did not engage"
        payload = {
            "residentId":    mc_resident_id,
            "facilityId":    self.facility_id,
            "noteCategory":  "ACTIVITY",
            "noteDate":      session_date,
            "noteText": (
                f"Activity: {activity_title}\n"
                f"Date: {session_date}\n"
                f"Engagement: {engaged_text}\n"
                f"Mood Before: {mood_labels.get(mood_before,'?')} ({mood_before}/5)\n"
                f"Mood After:  {mood_labels.get(mood_after,'?')} ({mood_after}/5)\n"
                f"Staff Observation: {staff_note or 'None'}\n"
                f"Recorded by ActivityPro at {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            ),
            "authoredBy": "ActivityPro Integration",
        }
        resp = requests.post(
            f"{self.base_url}/clinical/notes",
            json=payload,
            headers=self._headers(),
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def get_resident_diagnoses(self, mc_resident_id: str) -> list:
        """Pull active diagnoses for a resident (ICD-10 codes + descriptions)."""
        resp = requests.get(
            f"{self.base_url}/residents/{mc_resident_id}/diagnoses",
            headers=self._headers(),
            params={"status": "active"},
            timeout=10
        )
        resp.raise_for_status()
        return resp.json().get("diagnoses", [])


def get_matrixcare_client_from_secrets() -> "MatrixCareClient | None":
    """
    Build a MatrixCare client from Streamlit secrets.
    Returns None if credentials are not configured.
    """
    try:
        import streamlit as st
        ehr = st.secrets.get("ehr", {})
        api_key     = ehr.get("mc_api_key")
        facility_id = ehr.get("mc_facility_id")
        sandbox     = ehr.get("mc_sandbox", True)
        if not all([api_key, facility_id]):
            return None
        return MatrixCareClient(api_key, facility_id, sandbox)
    except Exception:
        return None
