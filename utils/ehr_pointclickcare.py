"""
PointClickCare EHR Integration Client
======================================
PointClickCare is the leading EHR platform in North American long-term care.

To use in production:
1. Apply for API access at https://pointclickcare.com/partners/
2. Obtain client_id, client_secret, and org_uuid from PCC developer portal
3. Add credentials to .streamlit/secrets.toml:
   [ehr]
   pcc_client_id = "your_client_id"
   pcc_client_secret = "your_client_secret"
   pcc_org_uuid = "your_org_uuid"
   pcc_sandbox = true

Sandbox base URL: https://sandbox.pointclickcare.com/api/public/v1
Production base URL: https://connect.pointclickcare.com/api/public/v1
"""
import requests
from datetime import datetime

SANDBOX_BASE = "https://sandbox.pointclickcare.com/api/public/v1"
PROD_BASE    = "https://connect.pointclickcare.com/api/public/v1"


class PointClickCareClient:
    def __init__(self, client_id: str, client_secret: str, org_uuid: str, sandbox: bool = True):
        self.client_id     = client_id
        self.client_secret = client_secret
        self.org_uuid      = org_uuid
        self.base_url      = SANDBOX_BASE if sandbox else PROD_BASE
        self._token        = None

    def _get_token(self) -> str:
        """OAuth 2.0 client credentials flow."""
        resp = requests.post(
            f"{self.base_url}/auth/token",
            data={
                "grant_type":    "client_credentials",
                "client_id":     self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=10
        )
        resp.raise_for_status()
        self._token = resp.json()["access_token"]
        return self._token

    def _headers(self) -> dict:
        if not self._token:
            self._get_token()
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type":  "application/json",
            "X-PCC-OrgUuid": self.org_uuid,
        }

    def get_residents(self) -> list:
        """
        Pull resident list from PCC facility.
        Returns list of dicts with pcc_id, firstName, lastName, roomNumber, dob.
        """
        resp = requests.get(f"{self.base_url}/patients", headers=self._headers(), timeout=10)
        resp.raise_for_status()
        return resp.json().get("data", [])

    def post_activity_note(self, pcc_patient_id: str, activity_title: str,
                           engagement: bool, mood_before: int, mood_after: int,
                           staff_note: str, session_date: str) -> dict:
        """
        Write an activity participation note to a resident's PCC chart.

        PCC accepts progress notes via the /progressNotes endpoint.
        The note is tagged as an Activity Note for the MDS section.
        """
        mood_labels = {1:"Very Low",2:"Low",3:"Neutral",4:"Good",5:"Great"}
        engaged_text = "Resident participated and engaged." if engagement else "Resident did not engage."
        note_text = (
            f"Activity: {activity_title}\n"
            f"Date: {session_date}\n"
            f"Engagement: {engaged_text}\n"
            f"Mood Before: {mood_labels.get(mood_before,'?')} ({mood_before}/5)\n"
            f"Mood After:  {mood_labels.get(mood_after,'?')} ({mood_after}/5)\n"
            f"Staff Observation: {staff_note or 'None'}\n"
            f"Recorded by ActivityPro at {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        payload = {
            "patientId":  pcc_patient_id,
            "noteType":   "ACTIVITY",
            "noteText":   note_text,
            "noteDate":   session_date,
        }
        resp = requests.post(
            f"{self.base_url}/progressNotes",
            json=payload,
            headers=self._headers(),
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def sync_resident_demographics(self, pcc_patient_id: str) -> dict:
        """Pull a single resident's demographics from PCC (name, DOB, diagnoses)."""
        resp = requests.get(
            f"{self.base_url}/patients/{pcc_patient_id}",
            headers=self._headers(),
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()


def get_pcc_client_from_secrets() -> "PointClickCareClient | None":
    """
    Build a PCC client from Streamlit secrets.
    Returns None if credentials are not configured.
    """
    try:
        import streamlit as st
        ehr = st.secrets.get("ehr", {})
        client_id     = ehr.get("pcc_client_id")
        client_secret = ehr.get("pcc_client_secret")
        org_uuid      = ehr.get("pcc_org_uuid")
        sandbox       = ehr.get("pcc_sandbox", True)
        if not all([client_id, client_secret, org_uuid]):
            return None
        return PointClickCareClient(client_id, client_secret, org_uuid, sandbox)
    except Exception:
        return None
