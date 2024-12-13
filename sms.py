import ovh
import json
import discord

# Wczytaj konfigurację z pliku config.json
with open("config.json", "r") as f:
    config = json.load(f)

# Konfiguracja klienta OVH
client = ovh.Client(
    endpoint='ovh-eu',  # Endpoint OVH API (np. 'ovh-eu' dla Europy)
    application_key=config["ovh_app_key"],  # Klucz aplikacji z config.json
    application_secret=config["ovh_app_secret"],  # Sekret aplikacji z config.json
    consumer_key=config["ovh_consumer_key"]  # Klucz użytkownika z config.json
)

def create_embed(title, description, success=True):
    """
    Tworzy embed z wiadomością sukcesu lub błędu.

    :param title: Tytuł embeda
    :param description: Opis embeda
    :param success: Czy jest to wiadomość sukcesu (domyślnie True)
    :return: Obiekt embeda Discord
    """
    color = discord.Color.green() if success else discord.Color.red()
    embed = discord.Embed(title=title, description=description, color=color)
    return embed

def send_sms(message=None):
    """
    Wysyła SMS za pomocą OVH API na podstawie danych z config.json.

    :param message: Treść wiadomości SMS (opcjonalnie, jeśli brak to używa default_sms_message z config.json)
    :return: Wynik w formacie embeda Discord
    """
    service_name = config["ovh_sms_service"]
    sender = "MQGRUZ.PL"  # Możesz zmienić na dowolną nazwę
    receivers = [config["sms_recipient"]]  # Odbiorca z config.json
    message = message or config["default_sms_message"]

    try:
        result = client.post(
            f"/sms/{service_name}/jobs",
            sender=sender,
            receivers=receivers,
            message=message,
            noStopClause=True,  # Opcja wyłączenia klauzuli STOP (wymaga wiadomości nie-reklamowej)
        )
        # Sprawdzenie wyników
        if result.get("validReceivers"):
            return create_embed("✅ Sukces!", "SMS wysłany pomyślnie do odbiorcy.", success=True)
        else:
            return create_embed(
                "❌ Błąd!",
                f"Nie udało się wysłać SMS: brak poprawnych odbiorców. Szczegóły: {json.dumps(result, indent=4)}",
                success=False
            )
    except ovh.exceptions.APIError as e:
        return create_embed("❌ Błąd API!", f"Błąd API OVH: {str(e)}", success=False)
    except Exception as e:
        return create_embed("❌ Nieoczekiwany błąd!", f"Nieoczekiwany błąd: {str(e)}", success=False)

# Przykład użycia w bota
if __name__ == "__main__":
    response_embed = send_sms()
    # Tutaj należy wysłać embeda przez bota Discord (np. message.channel.send(embed=response_embed))
    print(response_embed.to_dict())  # Wypisz dla testów strukturę embeda