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
    "2x2-mob": {"modo": "2x2 Mobile", "valor": "R$ 0,30", "jogadores": 4},
    "3x3-mob": {"modo": "3x3 Mobile", "valor": "R$ 0,40", "jogadores": 6},
    "4x4-mob": {"modo": "4x4 Mobile", "valor": "R$ 0,50", "jogadores": 8},
}

# Valores disponíveis para as próximas filas/painéis.
VALORES = [
    "R$ 0,20", "R$ 0,30", "R$ 0,40", "R$ 0,50",
    "R$ 0,75", "R$ 1,00", "R$ 2,00", "R$ 3,00",
    "R$ 5,00", "R$ 7,00", "R$ 10,00", "R$ 15,00",
    "R$ 20,00", "R$ 30,00", "R$ 50,00", "R$ 100,00",
]

filas = {nome: {"normal": set(), "infinito": set()} for nome in FILAS}

def descobrir_fila(channel):
    # Aceita canais com emojis/símbolos antes do nome, por exemplo:
    # "📱・2x2-mob" ou "📱 • 2x2-mob".
    nome = getattr(channel, "name", "").lower().strip()

    # Primeiro tenta o nome exato.
    for fila in FILAS:
        if nome == fila.lower():
            return fila

    # Depois procura o nome da fila no final do nome do canal.
    # Isso evita erro quando o canal tem emoji ou separador.
    for fila in FILAS:
        if nome.endswith(fila.lower()):
            return fila

    return None

def criar_embed(interaction, fila):
    c = FILAS[fila]
    f = filas[fila]

    normal = list(f["normal"])
    infinito = list(f["infinito"])

    embed = discord.Embed(
        title=f"🔥 {c['modo'].upper()} | ORG BOM E NOVO",
        description="━━━━━━━━━━━━━━━━━━━━\\n"
                    "🎯 **PAINEL DE FILA**\\n"
                    "Entre em uma das filas abaixo e aguarde a partida.\\n"
                    "━━━━━━━━━━━━━━━━━━━━",
    )

    embed.add_field(
        name="🎮 Modo",
        value=f"**{c['modo']}**",
        inline=True
    )
    embed.add_field(
        name="💰 Valor desta fila",
        value=f"**{c['valor']}**",
        inline=True
    )
    embed.add_field(
        name="👥 Vagas",
        value=f"**{c['jogadores']} jogadores**",
        inline=True
    )

    normal_texto = " ".join(f"<@{x}>" for x in normal) if normal else "Nenhum jogador"
    infinito_texto = " ".join(f"<@{x}>" for x in infinito) if infinito else "Nenhum jogador"

    embed.add_field(
        name="🧊 Gelo Normal",
        value=normal_texto,
        inline=False
    )
    embed.add_field(
        name="♾️ Gelo Infinito",
        value=infinito_texto,
        inline=False
    )

    valores_texto = " • ".join(VALORES)
    embed.add_field(
        name="💵 TODOS OS VALORES DISPONÍVEIS",
        value=valores_texto,
        inline=False
    )

    embed.set_footer(text="ORG BOM E NOVO • Escolha Gelo Normal ou Gelo Infinito")

    # Usa o avatar do próprio bot.
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

        # Se já está exatamente nesta fila/modo, avisa somente a própria pessoa.
        if uid in f[tipo]:
            await interaction.response.send_message(
                "⚠️ Você já está na fila!",
                ephemeral=True
            )
            return

        # Se estava no outro modo, troca para o modo clicado.
        outro = "infinito" if tipo == "normal" else "normal"
        f[outro].discard(uid)
        f[tipo].add(uid)

        nome = "Gelo Normal" if tipo == "normal" else "Gelo Infinito"
        limite = FILAS[self.fila]["jogadores"] // 2
        qtd = len(f[tipo])

        # Não cria mensagem embaixo do painel.
        await interaction.response.defer()

        # Atualiza o painel original, mostrando os @ dos jogadores.
        await interaction.message.edit(
            embed=criar_embed(interaction, self.fila),
            view=self
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
            await interaction.message.edit(
                embed=criar_embed(interaction, self.fila),
                view=self
            )

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
        await interaction.response.defer()
        await interaction.message.edit(
            embed=criar_embed(interaction, self.fila),
            view=self
        )

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
    
