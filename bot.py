import discord
from discord.ext import commands
import sqlite3
import asyncio
import time

# ================= CONFIG =================

TOKEN = "MTUxODYxNTA1MzU1MTgwMDQ0MA.Gr83Qx.xWT7wA67xU9MQZXs3rwEL3tghA9kFc1Sto8qTc"
PREFIX = "+-"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# ================= DATABASE =================

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS warns (
    user_id TEXT PRIMARY KEY,
    warns INTEGER
)
""")
conn.commit()

def get_warns(user_id):
    cursor.execute("SELECT warns FROM warns WHERE user_id = ?", (user_id,))
    r = cursor.fetchone()
    return r[0] if r else 0

def add_warn(user_id):
    atual = get_warns(user_id)
    if atual == 0:
        cursor.execute("INSERT INTO warns VALUES (?, ?)", (user_id, 1))
    else:
        cursor.execute("UPDATE warns SET warns = ? WHERE user_id = ?", (atual+1, user_id))
    conn.commit()
    return atual + 1

def reset_warns(user_id):
    cursor.execute("DELETE FROM warns WHERE user_id = ?", (user_id,))
    conn.commit()

# ================= ANTI-FLOOD =================

flood = {}
MENSAGENS = 5
TEMPO = 5
MUTE_TEMPO = 10

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    now = time.time()

    if user_id not in flood:
        flood[user_id] = []

    flood[user_id].append(now)

    flood[user_id] = [t for t in flood[user_id] if now - t <= TEMPO]

    if len(flood[user_id]) >= MENSAGENS:

        cargo = discord.utils.get(message.guild.roles, name="Mutado")

        if not cargo:
            cargo = await message.guild.create_role(name="Mutado")
            for canal in message.guild.channels:
                await canal.set_permissions(cargo, send_messages=False, speak=False)

        await message.author.add_roles(cargo)
        await message.channel.send(f"{message.author.mention} foi mutado por flood 🚫")

        await asyncio.sleep(MUTE_TEMPO)
        await message.author.remove_roles(cargo)

        flood[user_id] = []

    await bot.process_commands(message)

# ================= EVENTO =================

@bot.event
async def on_ready():
    print(f"✅ Bot online como {bot.user}")

# ================= MODERAÇÃO =================

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, membro: discord.Member, *, motivo):
    await membro.ban(reason=motivo)
    await ctx.send(f"{membro} foi banido.")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, membro: discord.Member, *, motivo):
    await membro.kick(reason=motivo)
    await ctx.send(f"{membro} foi expulso.")

@bot.command()
@commands.has_permissions(ban_members=True)
async def desban(ctx, user_id: int):
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)
    await ctx.send(f"{user} foi desbanido.")

# ================= WARN =================

@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, membro: discord.Member, *, motivo):
    total = add_warn(str(membro.id))

    try:
        await membro.send(f"⚠️ Aviso\nMotivo: {motivo}\nStaff: {ctx.author}")
    except:
        pass

    if total >= 5:
        await membro.ban(reason="5 avisos")
        reset_warns(str(membro.id))
        await ctx.send(f"{membro} foi banido por 5 avisos.")
    else:
        await ctx.send(f"{membro} agora tem {total}/5 avisos.")

# ================= MUTE =================

@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, membro: discord.Member, tempo: int, *, motivo):
    cargo = discord.utils.get(ctx.guild.roles, name="Mutado")

    if not cargo:
        cargo = await ctx.guild.create_role(name="Mutado")
        for canal in ctx.guild.channels:
            await canal.set_permissions(cargo, send_messages=False, speak=False)

    await membro.add_roles(cargo)
    await ctx.send(f"{membro} mutado por {tempo}s.")

    await asyncio.sleep(tempo)
    await membro.remove_roles(cargo)

@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, user_id: int):
    membro = await ctx.guild.fetch_member(user_id)
    cargo = discord.utils.get(ctx.guild.roles, name="Mutado")

    if cargo in membro.roles:
        await membro.remove_roles(cargo)
        await ctx.send(f"{membro} desmutado.")

# ================= LIMPAR CHAT =================

@bot.command()
@commands.has_permissions(manage_messages=True)
async def limpchat(ctx, quantidade: int):
    if quantidade > 100:
        return await ctx.send("Máximo 100 mensagens.")

    await ctx.channel.purge(limit=quantidade)
    msg = await ctx.send(f"{quantidade} mensagens apagadas.")
    await asyncio.sleep(3)
    await msg.delete()

# ================= PAINEL =================

@bot.command()
@commands.has_permissions(manage_guild=True)
async def painel(ctx):
    await ctx.send("""
🎛️ **PAINEL DE MODERAÇÃO**

Use os comandos:

+-ban @user motivo
+-kick @user motivo
+-mute @user tempo motivo
+-unmute ID
+-warn @user motivo
+-limpchat quantidade
""")

# ================= MEMBROS =================

@bot.command()
async def avatar(ctx, membro: discord.Member = None):
    membro = membro or ctx.author
    await ctx.send(membro.display_avatar.url)

@bot.command()
async def userinfo(ctx, membro: discord.Member = None):
    membro = membro or ctx.author
    await ctx.send(f"{membro} | ID: {membro.id}")

# ================= INTERAÇÃO =================

@bot.command()
async def abracar(ctx, membro: discord.Member):
    await ctx.send(f"{ctx.author} abraçou {membro} 🤗")

@bot.command()
async def beijar(ctx, membro: discord.Member):
    await ctx.send(f"{ctx.author} beijou {membro} 😘")

@bot.command()
async def tapa(ctx, membro: discord.Member):
    await ctx.send(f"{ctx.author} deu um tapa em {membro} 😂")

# ================= START =================

bot.run(TOKEN)