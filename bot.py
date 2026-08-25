import os
import re
import threading
import base64
import io
from flask import Flask
import discord
from discord.ext import commands

# Logo ORG DRACO compactada e embutida no código.
LOGO_B64 = """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"""

def criar_arquivo_logo():
    return discord.File(io.BytesIO(base64.b64decode(LOGO_B64)), filename="org_draco.webp")

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("A variável DISCORD_TOKEN não foi configurada.")

# =========================
# Render / servidor web
# =========================
app = Flask(__name__)

@app.get("/")
def home():
    return "Bot online!"

def run_web():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")))

threading.Thread(target=run_web, daemon=True).start()

# =========================
# Discord
# =========================
intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Cada canal representa um modo.
# O /painel daquele canal vai criar UMA mensagem para CADA valor.
FILAS = {
    "1x1-mob": {"modo": "1x1 Mobile", "jogadores": 2},
    "2x2-mob": {"modo": "2x2 Mobile", "jogadores": 4},
    "3x3-mob": {"modo": "3x3 Mobile", "jogadores": 6},
    "4x4-mob": {"modo": "4x4 Mobile", "jogadores": 8},
}

VALORES = sorted([
    "R$ 0,20",
    "R$ 0,30",
    "R$ 0,40",
    "R$ 0,50",
    "R$ 0,75",
    "R$ 1,00",
    "R$ 2,00",
    "R$ 3,00",
    "R$ 5,00",
    "R$ 7,00",
    "R$ 10,00",
    "R$ 15,00",
    "R$ 20,00",
    "R$ 30,00",
    "R$ 50,00",
    "R$ 100,00",
], key=lambda v: float(v.replace("R$ ", "").replace(".", "").replace(",", ".")), reverse=True)

# chave = (canal, valor)
# cada fila guarda os IDs dos jogadores separados por tipo.
filas = {
    (canal, valor): {"normal": [], "infinito": []}
    for canal in FILAS
    for valor in VALORES
}

def descobrir_fila(channel):
    nome = getattr(channel, "name", "").lower().strip()

    for fila in FILAS:
        if nome == fila.lower():
            return fila

    for fila in FILAS:
        if nome.endswith(fila.lower()):
            return fila

    return None

def chave_fila(fila, valor):
    return (fila, valor)

def formatar_jogadores(ids, tipo):
    nome_tipo = "Gelo Normal" if tipo == "normal" else "Gelo Infinito"

    if not ids:
        return "Nenhum jogador na fila"

    return "\n".join(
        f"👤 <@{uid}> | 🧊 {nome_tipo}"
        for uid in ids
    )

def criar_embed(fila, valor, tipo=None, ids=None):
    config = FILAS[fila]

    embed = discord.Embed(
        title=f"🔥 {config['modo'].upper()} | ORG DRACO",
        color=discord.Color.red(),
    )
    embed.set_thumbnail(url="attachment://org_draco.webp")

    embed.add_field(
        name="🎮 Modo",
        value=f"**{config['modo']}**",
        inline=False,
    )

    embed.add_field(
        name="💰 Valor",
        value=f"**{valor}**",
        inline=False,
    )

    if ids is None:
        estado = filas[chave_fila(fila, valor)]
        linhas = []

        if estado["normal"]:
            linhas.extend(
                f"👤 <@{uid}> | 🧊 Gelo Normal"
                for uid in estado["normal"]
            )

        if estado["infinito"]:
            linhas.extend(
                f"👤 <@{uid}> | ♾️ Gelo Infinito"
                for uid in estado["infinito"]
            )

        jogadores = "\n".join(linhas) if linhas else "Nenhum jogador na fila"
    else:
        jogadores = formatar_jogadores(ids, tipo)

    embed.add_field(
        name="👤 Jogadores",
        value=jogadores,
        inline=False,
    )

    return embed

class PartidaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ConfirmarPartidaButton())
        self.add_item(CancelarPartidaButton())


class ConfirmarPartidaButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Confirmar partida",
            style=discord.ButtonStyle.success,
            custom_id="partida_confirmar",
        )

    async def callback(self, interaction: discord.Interaction):
        # A confirmação é individual. Não removemos a View da mensagem,
        # pois os outros jogadores ainda precisam conseguir confirmar.
        await interaction.response.send_message(
            f"✅ {interaction.user.mention} **confirmou a partida!**",
            ephemeral=True,
        )


class CancelarPartidaButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Cancelar partida",
            style=discord.ButtonStyle.danger,
            custom_id="partida_cancelar",
        )

    async def callback(self, interaction: discord.Interaction):
        channel = interaction.channel
        await interaction.response.send_message(
            "❌ **Partida cancelada.** Esta sala será apagada.",
            ephemeral=True,
        )
        if channel is not None:
            await channel.delete(reason=f"Partida cancelada por {interaction.user}")


class FilaView(discord.ui.View):
    def __init__(self, fila, valor):
        super().__init__(timeout=None)
        self.fila = fila
        self.valor = valor

        # IDs únicos para cada mensagem/valor.
        self.add_item(EntrarButton(fila, valor, "normal"))
        self.add_item(EntrarButton(fila, valor, "infinito"))
        self.add_item(SairButton(fila, valor))

class EntrarButton(discord.ui.Button):
    def __init__(self, fila, valor, tipo):
        self.fila = fila
        self.valor = valor
        self.tipo = tipo

        if tipo == "normal":
            label = "🧊 Gelo Normal"
        else:
            label = "♾️ Gelo Infinito"

        safe = re.sub(r"[^a-z0-9]", "", valor.lower())
        custom_id = f"fila_entrar_{fila}_{safe}_{tipo}"

        super().__init__(
            label=label,
            style=discord.ButtonStyle.secondary,
            custom_id=custom_id[:100],
        )

    async def callback(self, interaction: discord.Interaction):
        await entrar_na_fila(
            interaction,
            self.fila,
            self.valor,
            self.tipo,
        )

class SairButton(discord.ui.Button):
    def __init__(self, fila, valor):
        self.fila = fila
        self.valor = valor

        safe = re.sub(r"[^a-z0-9]", "", valor.lower())
        custom_id = f"fila_sair_{fila}_{safe}"

        super().__init__(
            label="❌ Sair da fila",
            style=discord.ButtonStyle.danger,
            custom_id=custom_id[:100],
        )

    async def callback(self, interaction: discord.Interaction):
        uid = interaction.user.id
        estado = filas[chave_fila(self.fila, self.valor)]

        estado["normal"] = [x for x in estado["normal"] if x != uid]
        estado["infinito"] = [x for x in estado["infinito"] if x != uid]

        await interaction.response.edit_message(
            embed=criar_embed(self.fila, self.valor),
            view=FilaView(self.fila, self.valor),
        )

async def entrar_na_fila(interaction, fila, valor, tipo):
    uid = interaction.user.id
    estado = filas[chave_fila(fila, valor)]

    # Já está exatamente nessa fila.
    if uid in estado[tipo]:
        await interaction.response.send_message(
            "⚠️ **Você já está na fila!**",
            ephemeral=True,
        )
        return

    outro = "infinito" if tipo == "normal" else "normal"

    # Remove o jogador de qualquer outra fila desse mesmo modo/canal.
    for (f, v), fila_data in filas.items():
        if f == fila:
            fila_data["normal"] = [x for x in fila_data["normal"] if x != uid]
            fila_data["infinito"] = [x for x in fila_data["infinito"] if x != uid]

    estado[tipo].append(uid)

    limite = FILAS[fila]["jogadores"]

    # Atualiza a mensagem da fila imediatamente.
    embed_atualizado = criar_embed(fila, valor)
    await interaction.response.edit_message(
        embed=embed_atualizado,
        view=FilaView(fila, valor),
    )

    # Ainda não completou.
    if len(estado[tipo]) < limite:
        return

    # Fila completa: cria sala privada automaticamente.
    jogadores = list(estado[tipo])
    guild = interaction.guild

    if guild is None:
        return

    try:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
            ),
        }

        for player_id in jogadores:
            member = guild.get_member(player_id)
            if member:
                overwrites[member] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                )

        # Mantém a sala dentro da mesma categoria do canal da fila, quando possível.
        category = interaction.channel.category

        nome_tipo = "normal" if tipo == "normal" else "infinito"
        channel_name = f"partida-{fila}-{nome_tipo}-{re.sub(r'[^0-9a-z-]', '', valor.lower().replace('r$', '').replace(',', '-').replace(' ', ''))}"

        private_channel = await guild.create_text_channel(
            channel_name[:90],
            overwrites=overwrites,
            category=category,
            reason=f"Partida encontrada: {fila} {valor} {nome_tipo}",
        )

        embed_partida = criar_embed(
            fila,
            valor,
            tipo=tipo,
            ids=jogadores,
        )

        mentions = " ".join(f"<@{x}>" for x in jogadores)

        await private_channel.send(
            content=(
                f"🔥 **PARTIDA ENCONTRADA!**\n"
                f"{mentions}\n\n"
                f"Todos os jogadores da fila foram colocados nesta sala automaticamente."
            ),
            embed=embed_partida,
            view=PartidaView(),
            file=criar_arquivo_logo(),
        )

        # Limpa somente a fila que acabou de formar a partida.
        estado[tipo].clear()

        # Atualiza a mensagem pública sem os jogadores que acabaram de entrar.
        await interaction.message.edit(
            embed=criar_embed(fila, valor),
            view=FilaView(fila, valor),
        )

    except discord.Forbidden:
        await interaction.followup.send(
            "❌ Não consegui criar a sala privada. Dê ao bot a permissão **Gerenciar Canais**.",
            ephemeral=True,
        )
    except discord.HTTPException as e:
        await interaction.followup.send(
            f"❌ Não consegui criar a sala privada: `{e}`",
            ephemeral=True,
        )

async def registrar_views():
    bot.add_view(PartidaView())
    for fila in FILAS:
        for valor in VALORES:
            bot.add_view(FilaView(fila, valor))

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

@bot.tree.command(
    name="painel",
    description="Cria todas as filas de valores deste canal.",
)
async def painel(interaction: discord.Interaction):
    fila = descobrir_fila(interaction.channel)

    if not fila:
        canais = ", ".join(f"#{x}" for x in FILAS)
        await interaction.response.send_message(
            f"❌ Use /painel em um destes canais: {canais}",
            ephemeral=True,
        )
        return

    await interaction.response.send_message(
        f"✅ Criando as **{len(VALORES)} filas** de **{FILAS[fila]['modo']}**...",
        ephemeral=True,
    )

    # Uma mensagem separada para cada valor.
    for valor in VALORES:
        await interaction.channel.send(
            embed=criar_embed(fila, valor),
            view=FilaView(fila, valor),
            file=criar_arquivo_logo(),
        )

@bot.tree.command(
    name="limpar",
    description="Limpa as filas antigas deste canal.",
)
async def limparfila(interaction: discord.Interaction):
    fila = descobrir_fila(interaction.channel)

    if not fila:
        await interaction.response.send_message(
            "❌ Este canal não é uma fila.",
            ephemeral=True,
        )
        return

    for valor in VALORES:
        filas[chave_fila(fila, valor)]["normal"].clear()
        filas[chave_fila(fila, valor)]["infinito"].clear()

    # Apaga somente as mensagens de painel criadas pelo bot.
    # Mensagens normais dos jogadores não são removidas.
    apagadas = 0
    async for message in interaction.channel.history(limit=None):
        if message.author.id != bot.user.id:
            continue

        # Painéis de fila têm embed com o título do ORG DRACO e
        # componentes da FilaView. Não apaga outras mensagens do bot.
        eh_painel = (
            bool(message.embeds)
            and message.embeds[0].title
            and "ORG DRACO" in message.embeds[0].title
            and any(
                child.custom_id
                and child.custom_id.startswith(("fila_entrar_", "fila_sair_"))
                for child in getattr(message, "components", [])
                for row in [child]
                if hasattr(row, "children")
                for child in row.children
            )
        )

        if eh_painel:
            try:
                await message.delete()
                apagadas += 1
            except discord.HTTPExcept
