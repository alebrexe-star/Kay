import discord
from discord.ext import commands
import sqlite3
import asyncio
import time
import os

# ================= CONFIG =================

TOKEN = os.getenv("TOKEN")
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
        cursor.execute("UPDATE warns SET warns = ? WHERE user_id = ?", (atual + 1, user_id))

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
    if message.author.bot or not message.guild:
        return

    user_id = str(message.author.id)
    now = time.time()

    flood.setdefault(user_id, [])
    flood[user_id].append(now)

    flood[user_id] = [t for t in flood[user_id] if now - t <= TEMPO]

    if len(flood[user_id]) >= MENSAGENS:

        role = discord.utils.get(message.guild.roles, name="Mutado")

        if role is None:
            role = await message.guild.create_role(name="Mutado")

            for channel in message.guild.channels:
                try:
                    await channel.set_permissions(role, send_messages=False, speak=False)
                except:
                    pass

        try:
            await message.author.add_roles(role)
            await message.channel.send(f"{message.author.mention} foi mutado por flood 🚫")
        except:
            pass

        await asyncio.sleep(MUTE_TEMPO)

        try:
            await message.author.remove_roles(role)
        except:
            pass

        flood[user_id] = []

    await bot.process_commands(message)

# ================= EVENTO =================

@bot.event
async def on_ready():
    print(f"✅ Bot online como {bot.user}")

# ================= MODERAÇÃO =================

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, membro: discord.Member, *, motivo="Sem motivo"):
    await membro.ban(reason=motivo)
    await ctx.send(f"🔨 {membro} foi banido. Motivo: {motivo}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, membro: discord.Member, *, motivo="Sem motivo"):
    await membro.kick(reason=motivo)
    await ctx.send(f"👢 {membro} foi expulso. Motivo: {motivo}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def desban(ctx, user_id: int):
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)
    await ctx.send(f"✅ {user} foi desbanido.")

# ================= WARN =================

@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, membro: discord.Member, *, motivo="Sem motivo"):
    total = add_warn(str(membro.id))

    try:
        await membro.send(
            f"⚠️ Aviso\nMotivo: {motivo}\nStaff: {ctx.author}"
        )
    except:
        pass

    if total >= 5:
        await membro.ban(reason="5 avisos")
        reset_warns(str(membro.id))
        await ctx.send(f"🚨 {membro} foi banido por 5 avisos.")
    else:
        await ctx.send(f"⚠️ {membro} agora tem {total}/5 avisos.")

# ================= MUTE =================

@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, membro: discord.Member, tempo: int, *, motivo="Sem motivo"):
    role = discord.utils.get(ctx.guild.roles, name="Mutado")

    if role is None:
        role = await ctx.guild.create_role(name="Mutado")

        for channel in ctx.guild.channels:
            try:
                await channel.set_permissions(role, send_messages=False, speak=False)
            except:
                pass

    await membro.add_roles(role)
    await ctx.send(f"🔇 {membro} mutado por {tempo}s. Motivo: {motivo}")

    await asyncio.sleep(tempo)

    try:
        await membro.remove_roles(role)
    except:
        pass

@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, user_id: int):
    membro = await ctx.guild.fetch_member(user_id)
    role = discord.utils.get(ctx.guild.roles, name="Mutado")

    if role in membro.roles:
        await membro.remove_roles(role)
        await ctx.send(f"🔊 {membro} desmutado.")

# ================= LIMPAR CHAT =================

@bot.command()
@commands.has_permissions(manage_messages=True)
async def limpchat(ctx, quantidade: int):
    if quantidade > 100:
        return await ctx.send("❌ Máximo 100 mensagens.")

    await ctx.channel.purge(limit=quantidade)
    msg = await ctx.send(f"🧹 {quantidade} mensagens apagadas.")
    await asyncio.sleep(3)
    await msg.delete()

# ================= PAINEL =================

@bot.command()
@commands.has_permissions(manage_guild=True)
async def painel(ctx):
    await ctx.send("""
🎛️ PAINEL DE MODERAÇÃO

+-ban @user motivo
+-kick @user motivo
+-mute @user tempo motivo
+-unmute ID
+-warn @user motivo
+-limpchat quantidade
""")

# ================= INTERAÇÕES =================

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

if TOKEN is None:
    print("❌ TOKEN não encontrado! Configure variável de ambiente TOKEN")
else:
    bot.run(TOKEN)