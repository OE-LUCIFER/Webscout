import json
import aiohttp
from dataclasses import dataclass
from bs4 import BeautifulSoup
import tls_client
import random
from typing import ClassVar, NoReturn, List, Dict, Any
import requests

@dataclass
class DomainModel:
    name: str
    type: str
    forward_available: str
    forward_max_seconds: str


@dataclass
class CreateEmailResponseModel:
    email: str
    token: str


@dataclass
class MessageResponseModel:
    attachments: list | None
    body_html: str | None
    body_text: str | None
    cc: str | None
    created_at: str
    email_from: str | None
    id: str
    subject: str | None
    email_to: str | None


class TempMail:
    def __init__(self):
        self._session = aiohttp.ClientSession(
            base_url="https://api.internal.temp-mail.io",
            headers={
                'Host': 'api.internal.temp-mail.io',
                'User-Agent': 'okhttp/4.5.0',
                'Connection': 'close'
            }
        )

    async def close(self) -> None:
        if not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        return None

    async def get_domains(self) -> list[DomainModel]:
        async with self._session.get("/api/v3/domains") as response:
            response_json = await response.json()
            return [DomainModel(domain['name'], domain['type'], domain['forward_available'], domain['forward_max_seconds']) for domain in response_json['domains']]

    async def create_email(self, alias: str | None = None, domain: str | None = None) -> CreateEmailResponseModel:
        async with self._session.post("/api/v3/email/new", data={'name': alias, 'domain': domain}) as response:
            response_json = await response.json()
            return CreateEmailResponseModel(response_json['email'], response_json['token'])

    async def delete_email(self, email: str, token: str) -> bool:
        async with self._session.delete(f"/api/v3/email/{email}", data={'token': token}) as response:
            if response.status == 200:
                return True
            else:
                return False

    async def get_messages(self, email: str) -> list[MessageResponseModel] | None:
        async with self._session.get(f"/api/v3/email/{email}/messages") as response:
            response_json = await response.json()
            if len(response_json) == 0:
                return None
            return [MessageResponseModel(message['attachments'], message['body_html'], message['body_text'], message['cc'], message['created_at'], message['from'], message['id'], message['subject'], message['to']) for message in response_json]


class VNEngine:
    def __init__(self) -> NoReturn:
        self.lang: str = "?lang=en"
        self.base: str = "https://onlinesim.io/"
        self.endpoint: str = "api/v1/free_numbers_content/"
        self.country_url: str = f"{self.base}{self.endpoint}countries"

    def get_online_countries(self) -> List[Dict[str, str]]:
        response: Any = requests.get(url=self.country_url).json()
        if response["response"] == "1":
            all_countries: List[Dict[str, str]] = response["counties"]
            online_countries: List[Dict[str, str]] = list(
                filter(lambda x: x["online"] == True, all_countries)
            )
            return online_countries
        return []

    def get_country_numbers(self, country: str) -> List[Dict[str, str]]:
        numbers_url: str = f"{self.country_url}/{country}{self.lang}"
        response: Any = requests.get(url=numbers_url).json()
        if response["response"] == "1":
            numbers: List[Dict[str, str]] = list(
                map(lambda x: {"data_humans": x["data_humans"], "full_number": x["full_number"]}, response["numbers"])
            )
            return numbers
        return []

    def get_number_inbox(self, country: str, number: str) -> Dict[str, str]:
        number_detail_url: str = f"{self.country_url}/{country}/{number}{self.lang}"
        response: Any = requests.get(url=number_detail_url).json()
        if response["response"] != "1" or not response["online"]:
            print(f"Error: Unable to retrieve inbox messages for {country} - {number}")
            return {}

        messages: List[Dict[str, str]] = []
        for msg_data in response["messages"]["data"]:
            try:
                msg = {"data_humans": msg_data["data_humans"], "text": msg_data["text"]}
                messages.append(msg)
            except KeyError as e:
                print(f"Warning: Missing key '{str(e)}' in message data")

        return {"messages": messages}

class sms_message:
    def __init__(self, content, frm, time):
        self.content = content
        self.frm = frm
        self.time = time
