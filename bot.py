import os
import threading
from flask import Flask
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("A variável DISCORD_TOKEN não foi configurada.")

app = Flask(__name__)
@app.get("/")
def home():
    return "Bot online!"

def run_web():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
threading.Thread(target=run_web, daemon=True).start()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Um painel/fila separado para cada canal.
# Troque os nomes dos canais aqui se os seus forem diferentes.
FILAS = {
    "1x1-mob": {"modo": "1x1 Mobile", "valor": "R$ 0,20", "jogadores": 2},
    "2x2-mob": {"modo": "2x2 Mobile", "valor": "R$ 0,40", "jogadores": 4},
    "3x3-mob": {"modo": "3x3 Mobile", "valor": "R$ 0,60", "jogadores": 6},
    "4x4-mob": {"modo": "4x4 Mobile", "valor": "R$ 0,80", "jogadores": 8},
}

filas = {nome: {"normal": set(), "infinito": set()} for nome in FILAS}

def descobrir_fila(channel):
    nome = getattr(channel, "name", "").lower()
    return next((f for f in FILAS if f.lower() == nome), None)

def criar_embed(interaction, fila):
    c = FILAS[fila]
    embed = discord.Embed(
        title=f"🔥 {c['modo'].upper()} | SUA ORG",
        description=(
            f"🎮 **Modo:**\n{c['modo']}\n\n"
            f"💰 **Valor:**\n{c['valor']}\n\n"
            f"👥 **Jogadores:**\n{c['jogadores']}\n\n"
            "Escolha uma opção para entrar na fila."
        )
    )
    # Usa o avatar do próprio bot, nunca a imagem de outra organização.
    if interaction.client.user:
        embed.set_thumbnail(url=interaction.client.user.display_avatar.url)
    return embed

class FilaView(discord.ui.View):
    def __init__(self, fila):
        super().__init__(timeout=None)
        self.fila = fila

    async def entrar(self, interaction, tipo):
        uid = interaction.user.id
        f = filas[self.fila]
        f["normal"].discard(uid)
        f["infinito"].discard(uid)
        f[tipo].add(uid)
        nome = "Gelo Normal" if tipo == "normal" else "Gelo Infinito"
        limite = FILAS[self.fila]["jogadores"] // 2
        qtd = len(f[tipo])
        await interaction.response.send_message(
            f"✅ Você entrou na fila **{self.fila}** — **{nome}**.\n"
            f"👥 Jogadores: **{qtd}/{limite}**", ephemeral=True
        )
        if qtd >= limite:
            mentions = " ".join(f"<@{x}>" for x in f[tipo])
            await interaction.channel.send(
                f"🔥 **PARTIDA ENCONTRADA!**\n"
                f"Modo: **{FILAS[self.fila]['modo']}**\n"
                f"Tipo: **{nome}**\n"
                f"Jogadores: {mentions}"
            )
            f[tipo].clear()

    @discord.ui.button(label="🧊 Gelo Normal", style=discord.ButtonStyle.secondary, custom_id="gelo_normal")
    async def normal(self, interaction, button):
        await self.entrar(interaction, "normal")

    @discord.ui.button(label="🧊 Gelo Infinito", style=discord.ButtonStyle.secondary, custom_id="gelo_infinito")
    async def infinito(self, interaction, button):
        await self.entrar(interaction, "infinito")

    @discord.ui.button(label="❌ Sair da fila", style=discord.ButtonStyle.danger, custom_id="sair_fila")
    async def sair(self, interaction, button):
        uid = interaction.user.id
        filas[self.fila]["normal"].discard(uid)
        filas[self.fila]["infinito"].discard(uid)
        await interaction.response.send_message("✅ Você saiu da fila.", ephemeral=True)

@bot.event
async def on_ready():
    for fila in FILAS:
        bot.add_view(FilaView(fila))
    print(f"Bot conectado como {bot.user}")

@bot.tree.command(name="painel", description="Envia o painel da fila deste canal.")
async def painel(interaction):
    fila = descobrir_fila(interaction.channel)
    if not fila:
        canais = ", ".join(f"#{x}" for x in FILAS)
        await interaction.response.send_message(
            f"❌ Use /painel em um destes canais: {canais}", ephemeral=True
        )
        return
    await interaction.response.send_message(embed=criar_embed(interaction, fila), view=FilaView(fila))

@bot.tree.command(name="limparfila", description="Limpa a fila deste canal.")
async def limparfila(interaction):
    fila = descobrir_fila(interaction.channel)
    if not fila:
        await interaction.response.send_message("❌ Este canal não é uma fila.", ephemeral=True)
        return
    filas[fila]["normal"].clear()
    filas[fila]["infinito"].clear()
    await interaction.response.send_message(f"🧹 Fila **{fila}** limpa.", ephemeral=True)

@bot.event
async def setup_hook():
    await bot.tree.sync()

bot.run(TOKEN)
        
