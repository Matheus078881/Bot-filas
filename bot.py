import os
import re
import threading
from flask import Flask
import discord

# VERSAO FINAL 2026-08-16 - ordem decrescente + confirmacao de partida
from discord.ext import commands

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

VALORES = [
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
]

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
        title=f"🔥 {config['modo'].upper()} | ORG BOM E NOVO",
        description=(
            "🎯 **FILA DE PARTIDA**\n"
            "Entre na fila usando os botões abaixo.\n"
            "Quando a fila completar, uma sala privada será criada automaticamente."
        ),
    )

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

    embed.set_footer(text="ORG BOM E NOVO • Escolha Gelo Normal ou Gelo Infinito")
    return embed

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

class ConfirmacaoView(discord.ui.View):
    def __init__(self, jogadores):
        super().__init__(timeout=None)
        self.jogadores = set(jogadores)
        self.confirmados = set()

    def criar_embed(self):
        confirmados = list(self.confirmados)
        if confirmados:
            lista = "\n".join(f"👤 <@{uid}> — **Confirmou a partida!**" for uid in confirmados)
        else:
            lista = "Nenhum jogador confirmou ainda."

        embed = discord.Embed(
            title="✅ Partida Confirmada!",
            description=(
                lista + "\n\n"
                "*O outro jogador deverá confirmar a partida.*"
            )
        )
        return embed

    @discord.ui.button(label="✅ Confirmar partida", style=discord.ButtonStyle.success)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = interaction.user.id
        if uid not in self.jogadores:
            await interaction.response.send_message("❌ Você não participa desta partida.", ephemeral=True)
            return
        if uid in self.confirmados:
            await interaction.response.send_message("⚠️ Você já confirmou a partida!", ephemeral=True)
            return

        self.confirmados.add(uid)
        await interaction.response.edit_message(embed=self.criar_embed(), view=self)

    @discord.ui.button(label="❌ Cancelar partida", style=discord.ButtonStyle.danger)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in self.jogadores:
            await interaction.response.send_message("❌ Você não participa desta partida.", ephemeral=True)
            return
        await interaction.response.send_message("🗑️ Partida cancelada. Fechando a sala...", ephemeral=True)
        await interaction.channel.delete(reason="Partida cancelada pelos jogadores")


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

        confirm_view = ConfirmacaoView(jogadores)
        await private_channel.send(
            content=f"🔥 **PARTIDA ENCONTRADA!**\n{mentions}",
            embed=confirm_view.criar_embed(),
            view=confirm_view,
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

    # Discord coloca a mensagem mais nova embaixo; por isso criamos do menor para o maior.
    # Visualmente fica: 100,00 no topo e 0,20 embaixo.
    for valor in reversed(VALORES):
        await interaction.channel.send(
            embed=criar_embed(fila, valor),
            view=FilaView(fila, valor),
        )

@bot.tree.command(
    name="limparfila",
    description="Limpa todas as filas deste canal.",
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

    await interaction.response.send_message(
        f"🧹 Todas as filas de **{fila}** foram limpas.",
        ephemeral=True,
    )

@bot.event
async def setup_hook():
    await bot.tree.sync()
    await registrar_views()

bot.run(TOKEN)
                         
