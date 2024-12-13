import discord
from discord.ext import commands
from discord import app_commands
from sms import send_sms
import json
import yt_dlp
import asyncio
from datetime import datetime
from gambling import gambling_game

voice_clients = {}
# Wczytaj konfigurację
with open("config.json", "r") as f:
    config = json.load(f)

# Ustawienia bota
intents = discord.Intents.default()
intents.members = True  # Wymagane do zarządzania rolami
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix=commands.when_mentioned_or(), intents=intents)

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

# Funkcja pomocnicza do odtwarzania muzyki
async def play_music(voice_channel, url, guild_id):
    # Pobieranie audio za pomocą yt-dlp
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']

        # Połącz z kanałem głosowym
        vc = await voice_channel.connect()
        voice_clients[guild_id] = vc

        # Odtwarzanie audio
        vc.play(discord.FFmpegPCMAudio(executable="ffmpeg", source=audio_url))

        # Czekanie na zakończenie
        while vc.is_playing() or vc.is_paused():  # Upewnij się, że połączenie jest aktywne
            await asyncio.sleep(1)
    except Exception as e:
        print(f"Error playing music: {e}")
    finally:
        if guild_id in voice_clients and not vc.is_paused():  # Rozłącz tylko, jeśli nie wstrzymano
            await vc.disconnect()
            del voice_clients[guild_id]

# Komenda: muzyka
@bot.tree.command(name="muzyka", description="Odtwarza muzykę z podanego linku.")
@app_commands.describe(url="Link do muzyki (YouTube lub Spotify).")
async def muzyka(interaction: discord.Interaction, url: str):
    if not interaction.user.voice or not interaction.user.voice.channel:
        embed = create_embed("❌ Błąd!", "Musisz być na kanale głosowym, aby odtworzyć muzykę.", discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return

    voice_channel = interaction.user.voice.channel
    embed = create_embed("🎵 Muzyka", f"Odtwarzam: {url}", discord.Color.green())
    await interaction.response.send_message(embed=embed)

    try:
        await play_music(voice_channel, url, interaction.guild.id)
    except Exception as e:
        embed = create_embed("❌ Błąd!", f"Nie udało się odtworzyć muzyki: {e}", discord.Color.red())
        await interaction.followup.send(embed=embed)

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

# Komenda: kod
@bot.tree.command(name="kod", description="Wyświetla link do repozytorium GitHuba bota.")
async def kod(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📂 Kod źródłowy Pajac Bota",
        description="Kliknij [tutaj](https://github.com/MyMQL/Pajac-Bot), aby przejść do repozytorium na GitHubie.",
        color=discord.Color.blue()
    )
    embed.set_footer(text="Komenda stworzona dla deweloperów, proszę mi tam kurwa nie otwierać błędów")
    await interaction.response.send_message(embed=embed)

# Globalna zmienna do przechowywania połączeń głosowych

@bot.tree.command(name="pauza", description="Zatrzymuje aktualnie odtwarzaną muzykę.")
async def pauza(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    vc = voice_clients.get(guild_id)
    if vc and vc.is_playing():
        vc.pause()
        embed = create_embed("⏸ Pauza", "Muzyka została zatrzymana.")
        await interaction.response.send_message(embed=embed)
    else:
        embed = create_embed("❌ Błąd!", "Bot nie jest połączony z kanałem głosowym lub nie odtwarza muzyki.", discord.Color.red())
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name="dalej", description="Wznawia odtwarzanie zatrzymanej muzyki.")
async def dalej(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    vc = voice_clients.get(guild_id)  # Pobierz połączenie głosowe dla serwera
    if vc and vc.is_paused():
        vc.resume()
        embed = create_embed("▶️ Wznowienie", "Muzyka została wznowiona.")
        await interaction.response.send_message(embed=embed)
    elif vc and not vc.is_paused():
        embed = create_embed("❌ Błąd!", "Muzyka nie została wstrzymana, nic do wznowienia.", discord.Color.red())
        await interaction.response.send_message(embed=embed)
    else:
        embed = create_embed("❌ Błąd!", "Bot nie jest połączony z kanałem głosowym.", discord.Color.red())
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name="sms", description="Wyślij domyślny SMS.")
async def sms(interaction: discord.Interaction):
    # Sprawdzenie uprawnień administratora
    if not interaction.user.guild_permissions.administrator:
        embed = create_embed(
            "❌ Brak uprawnień!",
            "Musisz posiadać rolę z uprawnieniem administratora, aby wykonać to polecenie.",
            discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    try:
        # Pobierz embed z funkcji send_sms
        embed = send_sms()

        # Wyślij embed jako odpowiedź
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        embed = create_embed(
            "❌ Błąd!",
            f"Wystąpił nieoczekiwany błąd: {str(e)}",
            discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

        
@bot.tree.command(name="czystka", description="Usuwa x ostatnich wiadomości z czatu.")
@app_commands.describe(ilosc="Liczba wiadomości do usunięcia")
async def czystka(interaction: discord.Interaction, ilosc: int):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("Nie masz uprawnień do zarządzania wiadomościami!", ephemeral=True)
        return

    try:
        # Wyślij szybką odpowiedź na interakcję
        await interaction.response.send_message(f"Rozpoczynam usuwanie {ilosc} wiadomości...", ephemeral=True)

        # Usuń wiadomości
        deleted = await interaction.channel.purge(limit=ilosc)

        # Wyślij potwierdzenie w osobnym embedzie
        embed = create_embed(
            "🧹 Czystka!",
            f"Pomyślnie usunięto {len(deleted)} wiadomości.",
            discord.Color.green()
        )
        await interaction.followup.send(embed=embed)
    except Exception as e:
        embed = create_embed(
            "❌ Błąd!",
            f"Wystąpił błąd podczas usuwania wiadomości: {e}",
            discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)


# Automatyczne usuwanie wiadomości
@bot.event
async def on_message(message):
    auto_delete_channels = config.get("auto_delete_channels", [])

    if message.channel.id in auto_delete_channels:
        if not message.attachments:
            try:
                await message.delete()
                await message.author.send("Pisz na wiadomościach pajacu! Akceptujemy tylko załączniki.")
            except Exception as e:
                print(f"Nie udało się usunąć wiadomości: {e}")
        return

    await bot.process_commands(message)

# Komenda: ustaw_auto_usuwanie
@bot.tree.command(name="ustaw_auto_usuwanie", description="Dodaje kanał do listy automatycznego usuwania wiadomości.")
async def ustaw_auto_usuwanie(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Nie masz uprawnień administratora!", ephemeral=True)
        return

    try:
        auto_delete_channels = config.get("auto_delete_channels", [])
        if interaction.channel.id not in auto_delete_channels:
            auto_delete_channels.append(interaction.channel.id)
            config["auto_delete_channels"] = auto_delete_channels
            with open("config.json", "w") as f:
                json.dump(config, f, indent=4)

            await interaction.response.send_message(f"Kanał {interaction.channel.mention} został dodany do listy chronionych kanałów.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Kanał {interaction.channel.mention} jest już na liście chronionych kanałów.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Wystąpił błąd: {e}", ephemeral=True)

# Komenda: status
@bot.tree.command(name="status", description="Wyświetla status ZSTTP.")
async def status(interaction: discord.Interaction):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    description = (
        "Status ZSTTP: ✅ Nie wybuchła\n"
        "\n"
        "💡 **Automatyczne odświeżanie**\n"
        "Ostatnia aktualizacja: " + current_time
    )
    embed = create_embed("📊 Status ZSTTP", description, discord.Color.green())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="gambling", description="Uruchamia grę gambling z kołem fortuny.")
@app_commands.describe(options="Podaj od 2 do 4 opcji, oddzielając je przecinkami.")
async def gambling(interaction: discord.Interaction, *, options: str):
    options_list = [opt.strip() for opt in options.split(",") if opt.strip()]
    await gambling_game(interaction, options_list)

# Komenda: ochrona
@bot.tree.command(name="ochrona", description="Wyświetla listę chronionych kanałów.")
async def ochrona(interaction: discord.Interaction):
    auto_delete_channels = config.get("auto_delete_channels", [])

    if not auto_delete_channels:
        embed = create_embed(
            "📋 Chronione Kanały",
            "Nie ma żadnych chronionych kanałów.",
            discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return

    channel_mentions = [f"<#{channel_id}>" for channel_id in auto_delete_channels]
    description = "\n".join(channel_mentions)
    embed = create_embed(
        "📋 Chronione Kanały",
        f"Obecnie chronione kanały:\n{description}",
        discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

# Synchronizacja komend slash przy starcie
@bot.event
async def on_connect():
    await sync_commands()

# Uruchom bota
bot.run(config["token"])