from typing import ClassVar, NoReturn, List, Dict, Any
import requests

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

if __name__ == "__main__":
    vne = VNEngine()

    print("Available countries:")
    countries = vne.get_online_countries()
    for country in countries:
        print(f"- {country['name']}")

    country_name = input("Enter a country name (e.g., Russia, Spain): ")
    country_numbers = vne.get_country_numbers(country_name)
    if country_numbers:
        print(f"\nAvailable numbers for {country_name}:")
        for num in country_numbers:
            print(f"- {num['full_number']}")

    # Get a number from the user
    print("\nPlease select a number:")
    for i, num in enumerate(country_numbers, 1):
        print(f"{i}. {num['full_number']}")

    choice = int(input("Enter the number of your chosen option: ")) - 1
    selected_num = country_numbers[choice]['full_number']

    # Get inbox messages for the selected number
    inbox_messages = vne.get_number_inbox(country_name, selected_num)
    if inbox_messages:
        print(f"\nInbox messages for {country_name} - {selected_num}:")
        for msg in inbox_messages["messages"]:
            print(f"- {msg['data_humans']}: {msg['text']}")
    else:
        print("No inbox messages found.")