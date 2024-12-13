import random
import asyncio
import discord

def create_embed(title: str, description: str, color: discord.Color = discord.Color.blue()):
    """
    Tworzy embed z wiadomością.

    :param title: Tytuł embeda
    :param description: Opis embeda
    :param color: Kolor embeda (domyślnie niebieski)
    :return: Obiekt embeda Discord
    """
    return discord.Embed(title=title, description=description, color=color)

async def gambling_game(interaction: discord.Interaction, options: list):
    """
    Uruchamia grę gambling z kołem fortuny.

    :param interaction: Obiekt interakcji Discord
    :param options: Lista opcji (od 2 do 4 elementów)
    """
    if len(options) < 2 or len(options) > 4:
        embed = create_embed(
            "❌ Błąd!",
            "Musisz podać od 2 do 4 opcji, aby uruchomić grę.",
            discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    embed = create_embed(
        "🎰 Gambling Game",
        "Koło fortuny się kręci...",
        discord.Color.gold()
    )
    await interaction.response.send_message(embed=embed, ephemeral=False)
    message = await interaction.original_response()

    # Symulacja kręcenia się koła fortuny (dłuższy czas, szybsze zmiany)
    for _ in range(10):  # Więcej iteracji dla dłuższego efektu
        embed.description = f"Koło się kręci: {random.choice(options)}"
        await message.edit(embed=embed)
        await asyncio.sleep(0.5)  # Krótszy czas pomiędzy zmianami

    # Losowanie wyniku
    result = random.choice(options)
    result_embed = create_embed(
        "🎉 Wynik gry!",
        f"Wygrana opcja: **{result}**",
        discord.Color.green()
    )
    await interaction.followup.send(embed=result_embed)