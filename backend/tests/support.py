from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any

from fastapi import FastAPI
import httpx

from app.dependencies import get_current_user


def build_app(*routers, current_user: str = "tester@example.com") -> FastAPI:
    app = FastAPI()

    for router in routers:
        app.include_router(router)

    async def current_user_override() -> str:
        return current_user

    app.dependency_overrides[get_current_user] = current_user_override
    return app


async def request(app: FastAPI, method: str, url: str, **kwargs) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        return await client.request(method, url, **kwargs)


class FakeUserRepository:
    def __init__(self, users: list[dict[str, Any]] | None = None) -> None:
        self.users = {
            user["email"]: dict(user)
            for user in (users or [])
        }
        self.reset_codes: dict[str, dict[str, Any]] = {}
        self.created_users: list[dict[str, Any]] = []
        self.updated_passwords: list[tuple[str, str]] = []
        self.updated_fields: list[tuple[str, dict[str, Any]]] = []

    async def get_by_email(self, email: str) -> dict[str, Any] | None:
        user = self.users.get(email)
        return dict(user) if user is not None else None

    async def exists_by_email(self, email: str) -> bool:
        return email in self.users

    async def create(self, user: dict[str, Any]) -> dict[str, Any]:
        saved = dict(user)
        self.users[saved["email"]] = saved
        self.created_users.append(dict(saved))
        return dict(saved)

    async def update_fields(self, email: str, updates: dict[str, Any]) -> None:
        current = dict(self.users[email])
        current.update(updates)
        self.users[email] = current
        self.updated_fields.append((email, dict(updates)))

    async def update_password(self, email: str, hashed_password: str) -> None:
        self.users[email]["hashed_password"] = hashed_password
        self.updated_passwords.append((email, hashed_password))

    async def save_reset_code(self, email: str, code: str, expires_at: str) -> None:
        self.reset_codes[email] = {
            "email": email,
            "code": code,
            "expires_at": expires_at,
        }

    async def get_reset_code(self, email: str) -> dict[str, Any] | None:
        code = self.reset_codes.get(email)
        return dict(code) if code is not None else None

    async def delete_reset_code(self, email: str) -> None:
        self.reset_codes.pop(email, None)


class FakeConfigurationRepository:
    def __init__(self, items: list[dict[str, Any]] | None = None) -> None:
        self.items = [dict(item) for item in (items or [])]
        self.replaced_with: list[dict[str, Any]] | None = None
        self.created_payload: dict[str, Any] | None = None

    def list_all(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self.items]

    def get_by_id(self, configuration_id: str) -> dict[str, Any] | None:
        for item in self.items:
            if item["id"] == configuration_id:
                return dict(item)
        return None

    def replace_all(self, configurations: list[dict[str, Any]]) -> None:
        self.replaced_with = [dict(item) for item in configurations]
        self.items = [dict(item) for item in configurations]

    def create(self, configuration: dict[str, Any]) -> dict[str, Any]:
        self.created_payload = dict(configuration)
        self.items.append(dict(configuration))
        return dict(configuration)


class FakeProgramadorAtuacaoService:
    def __init__(self) -> None:
        self.sent_configurations: list[dict[str, Any]] = []
        self.logs: list[dict[str, Any]] = []

    def send_configuration(self, configuration: dict[str, Any]) -> None:
        self.sent_configurations.append(dict(configuration))

    def fetch_logs(self) -> list[dict[str, Any]]:
        return [deepcopy(log) for log in self.logs]


class FakeParticipantRepository:
    def __init__(self, participants: list[dict[str, Any]] | None = None) -> None:
        self.by_id: dict[str, dict[str, Any]] = {}
        self.by_email: dict[str, dict[str, Any]] = {}
        self.created: list[dict[str, Any]] = []
        self.updated: list[tuple[str, dict[str, Any]]] = []

        for participant in participants or []:
            self._store(participant)

    def _store(self, participant: dict[str, Any]) -> dict[str, Any]:
        saved = dict(participant)
        self.by_id[saved["id"]] = saved
        email = str(saved.get("email", "")).strip()
        if email:
            self.by_email[email] = saved
        return saved

    async def get_by_id(self, participant_id: str) -> dict[str, Any] | None:
        participant = self.by_id.get(participant_id)
        return dict(participant) if participant is not None else None

    async def get_by_email(self, email: str) -> dict[str, Any] | None:
        participant = self.by_email.get(email)
        return dict(participant) if participant is not None else None

    async def create(self, participant_data: dict[str, Any]) -> dict[str, Any]:
        saved = self._store(participant_data)
        self.created.append(dict(saved))
        return dict(saved)

    async def update_fields(
        self,
        participant_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any] | None:
        participant = self.by_id.get(participant_id)
        if participant is None:
            return None

        participant.update(updates)
        self._store(participant)
        self.updated.append((participant_id, dict(updates)))
        return dict(participant)


class FakeParticipantVideoRepository:
    def __init__(self, links: list[dict[str, Any]] | None = None) -> None:
        self.links = [dict(link) for link in (links or [])]
        self.linked_single_calls: list[dict[str, Any]] = []
        self.linked_many_calls: list[dict[str, Any]] = []

    async def list_by_participant(self, participant_id: str) -> list[dict[str, Any]]:
        return [
            dict(link)
            for link in self.links
            if link.get("participant_id") == participant_id
        ]

    async def get_by_id_and_participant(
        self,
        participant_id: str,
        video_id: str,
    ) -> dict[str, Any] | None:
        for link in self.links:
            linked_video_id = str(link.get("video_id") or link.get("id") or "")
            if link.get("participant_id") == participant_id and linked_video_id == video_id:
                return dict(link)
        return None

    async def link_participant_to_video(
        self,
        *,
        participant_id: str,
        video_id: str,
        associated_at: datetime,
        association_source: str,
    ) -> None:
        payload = {
            "participant_id": participant_id,
            "video_id": video_id,
            "associated_at": associated_at,
            "association_source": association_source,
        }
        self.links.append(dict(payload))
        self.linked_single_calls.append(dict(payload))

    async def link_participants_to_video(
        self,
        *,
        participant_ids: list[str],
        video_id: str,
        associated_at: datetime,
        association_source: str,
    ) -> list[str]:
        payload = {
            "participant_ids": list(participant_ids),
            "video_id": video_id,
            "associated_at": associated_at,
            "association_source": association_source,
        }
        self.linked_many_calls.append(dict(payload))

        for participant_id in participant_ids:
            self.links.append(
                {
                    "participant_id": participant_id,
                    "video_id": video_id,
                    "associated_at": associated_at,
                    "association_source": association_source,
                }
            )

        return list(participant_ids)


class FakeVideoRepository:
    def __init__(self, videos: list[dict[str, Any]] | None = None) -> None:
        self.videos = {
            video["id"]: dict(video)
            for video in (videos or [])
        }
        self.created: list[dict[str, Any]] = []
        self.raise_on_create: Exception | None = None
        self.update_returns_none = False
        self.uploaded_between_result: list[dict[str, Any]] | None = None

    async def create(self, video_document: dict[str, Any]) -> dict[str, Any]:
        if self.raise_on_create is not None:
            raise self.raise_on_create

        saved = dict(video_document)
        self.videos[saved["id"]] = saved
        self.created.append(dict(saved))
        return dict(saved)

    async def get_by_id(self, video_id: str) -> dict[str, Any] | None:
        video = self.videos.get(video_id)
        return dict(video) if video is not None else None

    async def list_by_ids(self, video_ids: list[str]) -> list[dict[str, Any]]:
        return [
            dict(self.videos[video_id])
            for video_id in video_ids
            if video_id in self.videos
        ]

    async def list_uploaded_between(
        self,
        start_at: datetime,
        end_at: datetime,
    ) -> list[dict[str, Any]]:
        if self.uploaded_between_result is not None:
            return [dict(video) for video in self.uploaded_between_result]

        items: list[dict[str, Any]] = []
        for video in self.videos.values():
            uploaded_at = video.get("uploaded_at")
            if uploaded_at is not None and start_at <= uploaded_at <= end_at:
                items.append(dict(video))
        return items

    async def update_file_metadata(
        self,
        video_id: str,
        file_data: dict[str, Any],
    ) -> dict[str, Any] | None:
        if self.update_returns_none:
            return None

        video = self.videos.get(video_id)
        if video is None:
            return None

        video.update(file_data)
        self.videos[video_id] = video
        return dict(video)


class FakeEventRepository:
    def __init__(self, participant_ids: list[str] | None = None) -> None:
        self.participant_ids = list(participant_ids or [])
        self.created_events: list[dict[str, Any]] = []
        self.calls: list[dict[str, Any]] = []

    async def create(self, event: dict[str, Any]) -> dict[str, Any]:
        self.created_events.append(dict(event))
        return dict(event)

    async def list_distinct_participant_ids_between(
        self,
        *,
        event_type: str,
        start_at: datetime,
        end_at: datetime,
    ) -> list[str]:
        self.calls.append(
            {
                "event_type": event_type,
                "start_at": start_at,
                "end_at": end_at,
            }
        )
        return list(self.participant_ids)


class FakeVideoFileRepository:
    def __init__(self) -> None:
        self.files: dict[str, dict[str, Any]] = {}
        self.deleted_file_ids: list[str] = []
        self.replace_calls: list[dict[str, Any]] = []
        self.file_counter = 0

    async def replace_file_for_video(
        self,
        *,
        video_id: str,
        filename: str,
        file_bytes: bytes,
        content_type: str,
    ) -> dict[str, Any]:
        self.file_counter += 1
        file_id = f"file-{self.file_counter}"
        payload = {
            "file_id": file_id,
            "filename": filename,
            "content_type": content_type,
            "size_bytes": len(file_bytes),
        }
        self.files[file_id] = {
            **payload,
            "content": file_bytes,
            "video_id": video_id,
        }
        self.replace_calls.append(
            {
                "video_id": video_id,
                "filename": filename,
                "content_type": content_type,
                "size_bytes": len(file_bytes),
            }
        )
        return dict(payload)

    async def get_file(self, file_id: str) -> dict[str, Any] | None:
        file_data = self.files.get(file_id)
        return dict(file_data) if file_data is not None else None

    async def delete_file(self, file_id: str) -> None:
        self.deleted_file_ids.append(file_id)
        self.files.pop(file_id, None)


class FakeDispatchRepository:
    def __init__(self) -> None:
        self.items: list[dict[str, Any]] = []

    async def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        saved = {
            "id": f"dispatch-{len(self.items) + 1}",
            **payload,
        }
        self.items.append(dict(saved))
        return dict(saved)


class FakeEmailSender:
    def __init__(self, delivery_mode: str = "outbox") -> None:
        self.delivery_mode = delivery_mode
        self.calls: list[dict[str, Any]] = []
        self.raise_error: Exception | None = None

    async def send_video_email(
        self,
        *,
        participant: dict[str, Any],
        video: dict[str, Any],
        video_file: dict[str, Any],
        reference_date,
    ) -> dict[str, str]:
        self.calls.append(
            {
                "participant": dict(participant),
                "video": dict(video),
                "video_file": dict(video_file),
                "reference_date": reference_date,
            }
        )
        if self.raise_error is not None:
            raise self.raise_error
        return {"delivery_mode": self.delivery_mode}
