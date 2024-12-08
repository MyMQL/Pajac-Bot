import discord
from discord.ext import commands
from discord import app_commands
import json

# Wczytaj konfigurację
with open("config.json", "r") as f:
    config = json.load(f)

# Ustawienia bota
intents = discord.Intents.default()
intents.members = True  # Wymagane do zarządzania rolami
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    activity = discord.Game(config["activity"])
    await bot.change_presence(status=getattr(discord.Status, config["status"]), activity=activity)
    print(f"Bot zalogowany jako {bot.user} i jest gotowy!")

# Funkcja pomocnicza do tworzenia embedów
def create_embed(title: str, description: str, color: discord.Color = discord.Color.blue()):
    embed = discord.Embed(title=title, description=description, color=color)
    return embed

# Funkcja do synchronizacji komend globalnych
async def sync_commands():
    await bot.tree.sync()
    print("Globalne komendy zostały zsynchronizowane!")

# Funkcja do synchronizacji komend dla konkretnego serwera (opcjonalnie)
async def sync_guild_commands(guild_id: int):
    guild = discord.Object(id=guild_id)
    await bot.tree.sync(guild=guild)
    print(f"Komendy dla serwera {guild_id} zostały zsynchronizowane!")

# Komenda: reset
@bot.tree.command(name="reset", description="Resetuje i synchronizuje komendy slash.")
async def reset(interaction: discord.Interaction):
    try:
        await sync_commands()
        embed = create_embed("🔄 Reset Komend", "Komendy zostały pomyślnie zsynchronizowane.")
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        embed = create_embed("❌ Błąd Resetu", f"Nie udało się zresetować komend: {e}", discord.Color.red())
        await interaction.response.send_message(embed=embed)

# Komenda: ping
@bot.tree.command(name="ping", description="Sprawdź ping bota.")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)  # Konwersja na ms
    embed = create_embed("🏓 Pong!", f"Ping bota: {latency}ms")
    await interaction.response.send_message(embed=embed)

# Komenda: obywatel
@bot.tree.command(name="obywatel", description="Nadaj użytkownikowi rolę obywatela.")
@app_commands.describe(user="Użytkownik, któremu chcesz nadać rolę.")
async def obywatel(interaction: discord.Interaction, user: discord.Member):
    role = interaction.guild.get_role(int(config["roles"]["citizen_role_id"]))
    if not role:
        embed = create_embed("Błąd!", "Nie znaleziono roli obywatela!", discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return
    try:
        await user.add_roles(role)
        embed = create_embed("Sukces!", f"Nadano rolę {role.mention} użytkownikowi {user.mention}.")
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        embed = create_embed("Błąd!", "Bot nie ma uprawnień, aby nadać tę rolę!", discord.Color.red())
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        embed = create_embed("Błąd!", f"Nie udało się nadać roli: {e}", discord.Color.red())
        await interaction.response.send_message(embed=embed)

# Komenda: wok
@bot.tree.command(name="wok", description="Pinguje określonego użytkownika.")
async def wok(interaction: discord.Interaction):
    user_id = int(config["users"]["wok_user_id"])
    user = await bot.fetch_user(user_id)
    if not user:
        embed = create_embed("Błąd!", "Nie znaleziono użytkownika do pingowania!", discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return
    embed = create_embed("Ping!", f"{user.mention}, zostałeś pingnięty!")
    await interaction.response.send_message(embed=embed)

# Komenda: obzarty
@bot.tree.command(name="obzarty", description="Pinguje określonego użytkownika.")
async def obzarty(interaction: discord.Interaction):
    user_id = int(config["users"]["obzarty_user_id"])
    user = await bot.fetch_user(user_id)
    if not user:
        embed = create_embed("Błąd!", "Nie znaleziono użytkownika do pingowania!", discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return
    embed = create_embed("Ping!", f"{user.mention}, zostałeś pingnięty!")
    await interaction.response.send_message(embed=embed)

# Komenda: mow
@bot.tree.command(name="mow", description="Powtarza w embedzie to, co napiszesz.")
@app_commands.describe(message="Wiadomość, którą bot ma powtórzyć.")
async def mow(interaction: discord.Interaction, message: str):
    embed = create_embed("📢 Wiadomość od bota", message)
    await interaction.response.send_message(embed=embed)

# Synchronizacja komend slash przy starcie
@bot.event
async def on_connect():
    await sync_commands()

# Uruchom bota
bot.run(config["token"])