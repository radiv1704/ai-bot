import aiohttp
import discord
from discord.ext import commands, tasks
import random, asyncio, json, datetime, os
import httpx
import os
import sys


# === Fancy Embed ===
def fancy_embed(title, description=None, color=discord.Color.blurple(), thumbnail=None, footer=None):
    embed = discord.Embed(title=title, description=description or "", color=color)
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    if footer:
        embed.set_footer(text=footer)
    return embed


# === Konfigurasi ===
TOKEN = "MTM2MTcxMjc0MjMzNTEyMzc5MQ.GfmGIo.iVIERHQ5dOgwVLRfDufckV-3WZVN8lqNY-8c8I"
PREFIX = "r!"
OPENROUTER_API_KEY = "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"
OPENROUTER_MODEL = "mistralai/mistral-7b-instruct"
OWNER_ID = 866642965929656320 # replace with your actual Discord ID

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# === Database sederhana ===
if not os.path.exists("data"):
    os.makedirs("data")
if not os.path.exists("data/warnings.json"):
    with open("data/warnings.json", "w") as f:
        json.dump({}, f)
if not os.path.exists("data/economy.json"):
    with open("data/economy.json", "w") as f:
        json.dump({}, f)
if not os.path.exists("data/xp.json"):
    with open("data/xp.json", "w") as f:
        json.dump({}, f)

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

# === Events ===
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} | ID: {bot.user.id}")
    print("Loaded commands:")
    for command in bot.commands:
        print(f"- {command.name}")

@bot.event
async def on_member_join(member):
    await member.send(f"Welcome to {member.guild.name}, {member.mention}!")
    role = discord.utils.get(member.guild.roles, name="Member")
    if role:
        await member.add_roles(role)

@bot.event
async def on_member_remove(member):
    channel = discord.utils.get(member.guild.text_channels, name="general")
    if channel:
        await channel.send(f"{member} has left the server.")

@bot.event
async def on_message(message):
    if not message.author.bot:
        # XP SYSTEM
        xp_data = load_json("data/xp.json")
        user_id = str(message.author.id)
        if user_id not in xp_data:
            xp_data[user_id] = {"xp": 0, "level": 1}
        xp_data[user_id]["xp"] += random.randint(2, 6)
        xp = xp_data[user_id]["xp"]
        level = xp_data[user_id]["level"]
        if xp >= level * 100:
            xp_data[user_id]["level"] += 1
            await message.channel.send(f"{message.author.mention} leveled up to {level + 1}!")
        save_json("data/xp.json", xp_data)

        # AI MENTION RESPONSE
        if bot.user in message.mentions:
            question = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
            if question:
                async with message.channel.typing():
                    headers = {
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "HTTP-Referer": "https://github.com/Radiv0317/BOT-BOT-BOT",
                        "X-Title": "UesagiBot"
                    }
                    payload = {
                        "model": OPENROUTER_MODEL,
                        "messages": [
                            {
                                "role": "system",
                                "content": (
                                    "You're a London roadman AI. Keep replies *very* short, chill, and slangy. "
                                    "Max 1-2 lines. Talk like you're jokin' with the mandem, init. "
                                    "Use phrases like 'safe', 'wagwan', 'man's gassed', 'lowkey', etc."
                                )
                            },
                            {"role": "user", "content": question}
                        ]
                    }
                    try:
                        async with httpx.AsyncClient() as client:
                            res = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
                            res.raise_for_status()
                            data = res.json()
                            answer = data["choices"][0]["message"]["content"]
                            await message.reply(answer.strip())
                    except httpx.HTTPStatusError as e:
                        error_text = await e.response.aread()
                        await message.channel.send(f"❌ HTTP {e.response.status_code}: `{error_text.decode()}`")
                    except Exception as e:
                        await message.channel.send(f"❌ Unexpected error: `{str(e)}`")

    await bot.process_commands(message)


    

# === Utility ===
@bot.command()
async def ping(ctx):
    async with ctx.typing():
        await asyncio.sleep(0.3)
        embed = fancy_embed("🏓 Pong!", f"Latency: `{round(bot.latency * 1000)}ms`", color=discord.Color.green())
        await ctx.send(embed=embed)


@bot.command()
async def avatar(ctx, member: discord.Member = None):
    async with ctx.typing():
        member = member or ctx.author
        embed = fancy_embed("🖼 Avatar", f"{member.mention}'s avatar", thumbnail=member.avatar.url)
        await ctx.send(embed=embed)


@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    async with ctx.typing():
        member = member or ctx.author
        embed = fancy_embed(
            "🧾 User Info",
            f"**👤 Name:** `{member.display_name}`\n**🆔 ID:** `{member.id}`\n**📅 Joined:** `{member.joined_at.strftime('%Y-%m-%d')}`\n**🧭 Created:** `{member.created_at.strftime('%Y-%m-%d')}`",
            thumbnail=member.avatar.url,
            footer=f"Requested by {ctx.author.display_name}"
        )
        await ctx.send(embed=embed)


@bot.command()
async def serverinfo(ctx):
    async with ctx.typing():
        guild = ctx.guild
        embed = fancy_embed(
            "🏰 Server Info",
            f"**📛 Name:** `{guild.name}`\n**👥 Members:** `{guild.member_count}`\n**🆔 ID:** `{guild.id}`",
            thumbnail=guild.icon.url if guild.icon else None,
            footer=f"Requested by {ctx.author.display_name}"
        )
        await ctx.send(embed=embed)


# === Moderation ===
@bot.command()
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount+1)
    await ctx.send(f"Deleted {amount} messages.", delete_after=3)

@bot.command()
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"{member} has been kicked.")

@bot.command()
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"{member} has been banned.")

@bot.command()
async def mute(ctx, member: discord.Member):
    mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not mute_role:
        mute_role = await ctx.guild.create_role(name="Muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(mute_role, speak=False, send_messages=False)
    await member.add_roles(mute_role)
    await ctx.send(f"{member.mention} has been muted.")

@bot.command()
async def unmute(ctx, member: discord.Member):
    mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
    await member.remove_roles(mute_role)
    await ctx.send(f"{member.mention} has been unmuted.")

@bot.command()
async def warn(ctx, member: discord.Member, *, reason):
    data = load_json("data/warnings.json")
    uid = str(member.id)
    if uid not in data:
        data[uid] = []
    data[uid].append(reason)
    save_json("data/warnings.json", data)
    await ctx.send(f"{member} has been warned: {reason}")

@bot.command()
async def warnings(ctx, member: discord.Member):
    data = load_json("data/warnings.json")
    uid = str(member.id)
    warns = data.get(uid, [])
    if not warns:
        await ctx.send("No warnings.")
    else:
        await ctx.send(f"{member} has {len(warns)} warning(s):\n" + "\n".join(warns))

@bot.command()
async def clearwarns(ctx, member: discord.Member):
    data = load_json("data/warnings.json")
    uid = str(member.id)
    data[uid] = []
    save_json("data/warnings.json", data)
    await ctx.send(f"Cleared warnings for {member}.")

@bot.command()
async def roll(ctx):
    result = random.randint(1, 100)
    embed = fancy_embed("🎲 You Rolled!", f"You rolled a `{result}`!", color=discord.Color.orange())
    await ctx.send(embed=embed)

@bot.command()
async def coinflip(ctx):
    result = random.choice(["Heads", "Tails"])
    embed = fancy_embed("🪙 Coin Flip", f"The coin landed on **{result}**!", color=discord.Color.gold())
    await ctx.send(embed=embed)

@bot.command()
async def joke(ctx):
    jokes = [
        "Why don't skeletons fight each other? They don't have the guts.",
        "I told my computer I needed a break, and it said 'No problem, I'll go to sleep.'",
        "Why was the math book sad? It had too many problems."
    ]
    joke = random.choice(jokes)
    embed = fancy_embed(joke, color=discord.Color.purple())
    await ctx.send(embed=embed)


@bot.command()
async def balance(ctx):
    data = load_json("data/economy.json")
    uid = str(ctx.author.id)
    bal = data.get(uid, 0)
    embed = fancy_embed("💰 Balance", f"{ctx.author.mention}, you have `${bal}`.", color=discord.Color.green())
    await ctx.send(embed=embed)

@bot.command()
async def work(ctx):
    data = load_json("data/economy.json")
    uid = str(ctx.author.id)
    amount = random.randint(50, 150)
    data[uid] = data.get(uid, 0) + amount
    save_json("data/economy.json", data)
    embed = fancy_embed("🛠️ Work Complete", f"You earned `${amount}` for your work!", color=discord.Color.green())
    await ctx.send(embed=embed)

@bot.command()
async def daily(ctx):
    data = load_json("data/economy.json")
    uid = str(ctx.author.id)
    now = datetime.datetime.now()
    if "last_daily" not in data:
        data["last_daily"] = {}
    last = data["last_daily"].get(uid)
    if last:
        last_time = datetime.datetime.fromisoformat(last)
        if (now - last_time).total_seconds() < 86400:
            embed = fancy_embed("⏳ Daily", "You already claimed your daily reward.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
    data[uid] = data.get(uid, 0) + 500
    data["last_daily"][uid] = now.isoformat()
    save_json("data/economy.json", data)
    embed = fancy_embed("🎁 Daily Reward", "You received your `$500` daily reward!", color=discord.Color.green())
    await ctx.send(embed=embed)

@bot.command()
async def give(ctx, member: discord.Member, amount: int):
    data = load_json("data/economy.json")
    uid = str(ctx.author.id)
    tid = str(member.id)
    if data.get(uid, 0) < amount:
        embed = fancy_embed("❌ Transaction Failed", "You don't have enough money.", color=discord.Color.red())
        await ctx.send(embed=embed)
        return
    data[uid] -= amount
    data[tid] = data.get(tid, 0) + amount
    save_json("data/economy.json", data)
    embed = fancy_embed("✅ Money Sent", f"You gave `${amount}` to **{member.display_name}**.", color=discord.Color.green())
    await ctx.send(embed=embed)


@bot.command()
async def rank(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = load_json("data/xp.json")
    uid = str(member.id)
    xp = data.get(uid, {"xp": 0, "level": 1})
    embed = fancy_embed("📊 Rank", f"**{member.display_name}**\nLevel: `{xp['level']}` | XP: `{xp['xp']}`", color=discord.Color.blue())
    await ctx.send(embed=embed)

@bot.command()
async def leaderboard(ctx):
    data = load_json("data/xp.json")
    sorted_users = sorted(data.items(), key=lambda x: x[1]["xp"], reverse=True)[:5]
    msg = ""
    for i, (uid, stats) in enumerate(sorted_users, 1):
        user = await bot.fetch_user(int(uid))
        msg += f"**{i}. {user.display_name}** - Level `{stats['level']}` ({stats['xp']} XP)\n"
    embed = fancy_embed("🏆 Leaderboard", msg.strip(), color=discord.Color.blue())
    await ctx.send(embed=embed)

@bot.command()
async def guess(ctx, tebakan: int):
    angka = random.randint(1, 10)
    if tebakan == angka:
        embed = fancy_embed("🎉 Tebak Angka", f"Benar! Angkanya adalah `{angka}`", color=discord.Color.green())
    else:
        embed = fancy_embed("❌ Tebak Angka", f"Salah! Aku pilih `{angka}`, bukan `{tebakan}`", color=discord.Color.red())
    await ctx.send(embed=embed)


@bot.command()
async def rps(ctx, pilihan: str):
    pilihan = pilihan.lower()
    if pilihan not in ["rock", "paper", "scissors"]:
        await ctx.send("Pilih antara: rock, paper, atau scissors.")
        return

    bot_pilihan = random.choice(["rock", "paper", "scissors"])
    hasil = ""

    if pilihan == bot_pilihan:
        hasil = "Seri!"
    elif (pilihan == "rock" and bot_pilihan == "scissors") or \
         (pilihan == "paper" and bot_pilihan == "rock") or \
         (pilihan == "scissors" and bot_pilihan == "paper"):
        hasil = "Kamu menang!"
    else:
        hasil = "Aku menang!"

    embed = fancy_embed("✊ Rock Paper Scissors", f"Kamu: `{pilihan}`\nAku: `{bot_pilihan}`\n\n**{hasil}**")
    await ctx.send(embed=embed)

# == AI ==
@bot.command()
async def ask(ctx, *, question: str):
    async with ctx.typing():
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://github.com/Radiv0317/BOT-BOT-BOT",  # WAJIB! URL bebas, tapi valid
            "X-Title": "UesagiBot"
        }

        payload = {
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "user", "content": question}
            ]
        }

        try:
            async with httpx.AsyncClient() as client:
                res = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                answer = data["choices"][0]["message"]["content"]
                embed = fancy_embed("🤖 AI Response", answer.strip(), color=discord.Color.teal())
                await ctx.send(embed=embed)

        except httpx.HTTPStatusError as e:
            error_text = await e.response.aread()
            await ctx.send(f"❌ HTTP {e.response.status_code}: `{error_text.decode()}`")
        except Exception as e:
            await ctx.send(f"❌ Unexpected error: `{str(e)}`")

@bot.command()
async def shutdown(ctx):
    if ctx.author.id != OWNER_ID:
        return await ctx.send("🚫 Nah fam, you ain't got the keys.")

    async with ctx.typing():
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://github.com/Radiv0317/BOT-BOT-BOT",
            "X-Title": "UesagiBot"
        }
        payload = {
            "model": OPENROUTER_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You're a UK roadman bot. Respond very short and chill. "
                        "Bot's shutting down 'cause boss said so. Use slang."
                    )
                },
                {"role": "user", "content": "Yo, shutdown bruv."}
            ]
        }

        try:
            async with httpx.AsyncClient() as client:
                res = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                response = data["choices"][0]["message"]["content"]
                await ctx.send(response.strip())
        except Exception as e:
            print(f"[ERROR] Shutdown response failed: {e}")
            await ctx.send("Offski, safe g. 👋")

    await bot.close()

@bot.command()
async def turnon(ctx):
    if ctx.author.id != OWNER_ID:
        return await ctx.send("Bruv you can’t bring me to life, you ain’t the plug 🔌.")
    await ctx.send("I’m already live fam, wagwan? 🔥")
# === RUN ===
bot.run(TOKEN)
