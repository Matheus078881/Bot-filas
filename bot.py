import os
import threading
from flask import Flask
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("A variável DISCORD_TOKEN não foi configurada.")

# Servidor simples para o Render manter o serviço ativo.
app = Flask(__name__)

@app.get("/")
def home():
    return "Bot online!"

def run_web():
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web, daemon=True).start()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

class ModoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def escolher(self, interaction: discord.Interaction, modo: str):
        await interaction.response.send_message(
            f"✅ Você selecionou **{modo}**.",
            ephemeral=True
        )

    @discord.ui.button(label="1v1", style=discord.ButtonStyle.primary, custom_id="modo_1v1")
    async def um(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.escolher(interaction, "1v1")

    @discord.ui.button(label="2v2", style=discord.ButtonStyle.success, custom_id="modo_2v2")
    async def dois(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.escolher(interaction, "2v2")

    @discord.ui.button(label="3v3", style=discord.ButtonStyle.secondary, custom_id="modo_3v3")
    async def tres(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.escolher(interaction, "3v3")

    @discord.ui.button(label="4v4", style=discord.ButtonStyle.danger, custom_id="modo_4v4")
    async def quatro(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.escolher(interaction, "4v4")


@bot.event
async def on_ready():
    bot.add_view(ModoView())
    print(f"Bot conectado como {bot.user}")


@bot.tree.command(name="painel", description="Envia o painel de modos 1v1, 2v2, 3v3 e 4v4.")
async def painel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎮 PAINEL DE PARTIDAS",
        description="Escolha o modo da sua partida:",
    )
    embed.add_field(name="⚔️ 1v1", value="1 jogador contra 1 jogador", inline=False)
    embed.add_field(name="👥 2v2", value="2 jogadores contra 2 jogadores", inline=False)
    embed.add_field(name="👥 3v3", value="3 jogadores contra 3 jogadores", inline=False)
    embed.add_field(name="🔥 4v4", value="4 jogadores contra 4 jogadores", inline=False)

    await interaction.response.send_message(embed=embed, view=ModoView())


async def sync_commands():
    await bot.tree.sync()

@bot.event
async def setup_hook():
    await sync_commands()

bot.run(TOKEN)
