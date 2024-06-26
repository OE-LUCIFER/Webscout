import aiohttp
from dataclasses import dataclass
from bs4 import BeautifulSoup
import tls_client
import random


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


class Client:
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

    async def __aexit__(self) -> None:
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


class TemporaryPhoneNumber:
    def __init__(self):
        self.maxpages = {"UK": 59, "US": 3, "France": 73, "Netherlands": 60, "Finland": 47}
        self.minpages = {"UK": 20, "US": 1, "France": 20, "Netherlands": 20, "Finland": 20}
        self.plist = {"UK": "+44", "US": "+1", "France": "+33", "Netherlands": "+31", "Finland": "+358"}
        self.countries = {"44": "UK", "1": "US", "33": "France", "31": "Netherlands", "358": "Finland"}

    def get_number(self, country="UK"):
        if country == "Random":
            country = random.choice(list(self.countries.values()))
        if country not in self.countries.values():
            raise ValueError("Unsupported Country")

        session = tls_client.Session(client_identifier="chrome112", random_tls_extension_order=True)
        maxpage = self.maxpages[country]
        minpage = self.minpages[country]
        page = random.randint(minpage, maxpage)

        if page == 1:
            res = session.get(f"https://temporary-phone-number.com/{country}-Phone-Number")
        else:
            res = session.get(f"https://temporary-phone-number.com/{country}-Phone-Number/page{page}")

        soup = BeautifulSoup(res.content, "lxml")
        numbers = []
        p = self.plist[country]
        for a in soup.find_all("a"):
            a = a.get("title", "none")
            if f"{country} Phone Number {p}" in a:
                a = a.replace(f"{country} Phone Number ", "").replace(" ", "")
                numbers.append(a)
        return random.choice(numbers)

    def get_messages(self, number: str):
        number = number.replace("+", "")
        try:
            i = int(number)
        except:
            raise ValueError("Wrong Number")

        country = None
        for key, value in self.countries.items():
            if number.startswith(key):
                country = value

        if country == None:
            raise ValueError("Unsupported Country")

        session = tls_client.Session(client_identifier="chrome112", random_tls_extension_order=True)
        res = session.get(f"https://temporary-phone-number.com/{country}-Phone-Number/{number}")

        if res.status_code == 404:
            raise ValueError("Number doesn't exist")

        soup = BeautifulSoup(res.content, "lxml")
        messages = []
        message = {"content": None, "frm": "", "time": ""}

        for div in soup.find_all("div"):
            divclass = div.get("class", "None")[0]
            if divclass == "direct-chat-info":
                message["frm"] = div.text.split("\n")[1].replace("From ", "")
                message["time"] = div.text.split("\n")[2]
            if divclass == "direct-chat-text":
                message["content"] = div.text
                messages.append(sms_message(content=message["content"], frm=message["frm"], time=message["time"]))
                message = {"content": None, "frm": "", "time": ""}

        return messages


class sms_message:
    def __init__(self, content, frm, time):
        self.content = content
        self.frm = frm
        self.time = time