import os
from typing import Any

import httpx


class ProgramadorAtuacaoIntegrationError(Exception):
    """Raised when the Programador de Atuação API call fails or returns a non-200 status."""

    def __init__(self, message: str, status_code: int) -> None:
        """
        Store the message and the HTTP status code to be forwarded to the caller.

        Args:
            message (str): Human-readable description of the failure.
            status_code (int): HTTP status code to be returned by the API endpoint.

        Returns:
            None.
        """
        super().__init__(message)
        self.status_code = status_code


class ProgramadorAtuacaoService:
    """Handle HTTP communication with the Programador de Atuação external API."""

    _BASE_URL_ENV = "PROGRAMADOR_ATUACAO_BASE_URL"
    _PARAMETRIZAR_PATH = "/parametrizar"
    _LOGS_PATH = "/logs"
    _CONNECTION_FAILURE_STATUS = 502

    def __init__(self) -> None:
        """
        Load the base URL from the environment.

        Raises:
            RuntimeError: When the required environment variable is not set.
        """
        base_url = os.getenv(self._BASE_URL_ENV)

        if not base_url:
            raise RuntimeError(
                f"Environment variable '{self._BASE_URL_ENV}' is not set."
            )

        self._base_url = base_url.rstrip("/")

    def send_configuration(self, configuration: dict) -> None:
        """
        Submit a configuration to the Programador de Atuação parametrize endpoint.

        Args:
            configuration (dict): The configuration payload to be sent.

        Returns:
            None.

        Raises:
            ProgramadorAtuacaoIntegrationError: With status 502 when the TCP connection
                cannot be established, or with the API's own status code when it
                rejects the request.
        """
        url = f"{self._base_url}{self._PARAMETRIZAR_PATH}"

        try:
            response = httpx.post(url, json=configuration)
        except httpx.RequestError as exc:
            raise ProgramadorAtuacaoIntegrationError(
                message=f"Failed to reach Programador de Atuação at '{url}': {exc}",
                status_code=self._CONNECTION_FAILURE_STATUS,
            ) from exc

        if response.status_code != httpx.codes.OK:
            raise ProgramadorAtuacaoIntegrationError(
                message=(
                    f"Programador de Atuação rejected the configuration. "
                    f"Status: {response.status_code}. Body: {response.text}"
                ),
                status_code=response.status_code,
            )

    def fetch_logs(self) -> list[dict[str, Any]]:
        """
        Fetch operation log events from the Programador de Atuação logs endpoint.

        Args:
            None.

        Returns:
            list[dict[str, Any]]: Raw list of log event dicts as returned by the API.

        Raises:
            ProgramadorAtuacaoIntegrationError: With status 502 when the TCP connection
                cannot be established, or with the API's own status code when it
                rejects the request.
        """
        url = f"{self._base_url}{self._LOGS_PATH}"

        try:
            response = httpx.get(url)
        except httpx.RequestError as exc:
            raise ProgramadorAtuacaoIntegrationError(
                message=f"Failed to reach Programador de Atuação at '{url}': {exc}",
                status_code=self._CONNECTION_FAILURE_STATUS,
            ) from exc

        if response.status_code != httpx.codes.OK:
            raise ProgramadorAtuacaoIntegrationError(
                message=(
                    f"Programador de Atuação returned an unexpected status. "
                    f"Status: {response.status_code}. Body: {response.text}"
                ),
                status_code=response.status_code,
            )

        return response.json()