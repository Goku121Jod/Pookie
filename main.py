import discord
from discord.ext import commands
import json
import asyncio

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.dm_messages = True
bot = commands.Bot(command_prefix='$', intents=intents)

# REMOVE default help command
bot.remove_command("help")

# User balances
balances = {}

# Helper to convert $ to LTC
def usd_to_ltc(usd):
    return round(float(usd) / 85.0, 4)

# --- Commands ---

@bot.command()
async def tip(ctx, member: discord.Member, amount: str):
    if not amount.startswith('$'):
        return await ctx.send("Amount must be in $ format, e.g., $5")
    usd = float(amount[1:])
    ltc = usd_to_ltc(usd)

    balances[str(member.id)] = balances.get(str(member.id), 0.0) + ltc

    msg = config["messages"]["tip_message"].replace("{sender}", ctx.author.mention)\
                                          .replace("{receiver}", member.mention)\
                                          .replace("{ltc}", f"{ltc:.4f}")\
                                          .replace("{usd}", f"${usd:.2f}")
    await ctx.send(msg)

@bot.command(aliases=["bals", "bal", "bal_ltc"])
async def balance(ctx):
    ltc = balances.get(str(ctx.author.id), 0.0)
    usd = round(ltc * 85, 2)
    bal_text = config["messages"]["bal_embed"]\
        .replace("{ltc}", f"{ltc:.4f}")\
        .replace("{usd}", f"${usd:.2f}")

    embed = discord.Embed(
        title=f"{ctx.author.display_name}'s Litecoin wallet",
        description=bal_text,
        color=0xFFFFFF  # White
    )
    await ctx.send(embed=embed)

@bot.command()
async def withdraw(ctx, currency: str = None):
    if ctx.guild is not None:
        return await ctx.send("Please DM me to use this command.")

    await ctx.send("Give your LTC address (must reply with ping):")

    def check_address(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        address_msg = await bot.wait_for('message', timeout=60.0, check=check_address)
        await ctx.send("How much is the amount? If all, then reply with all.")

        def check_amount(m):
            return m.author == ctx.author and m.channel == ctx.channel

        amount_msg = await bot.wait_for('message', timeout=60.0, check=check_amount)
        user_id = str(ctx.author.id)
        ltc_balance = balances.get(user_id, 0.0)

        if amount_msg.content.lower() == 'all':
            embed = discord.Embed(
                title="🚫 Command error",
                description="Cannot make a withdrawal at this moment.\nPlease try again later.",
                color=0xe74c3c
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("Manual amount withdrawal is not supported.")

    except asyncio.TimeoutError:
        await ctx.send("Timed out. Please try again.")

@bot.command()
async def setbal(ctx, member: discord.Member, amount: str):
    if str(ctx.author.id) not in config["owner_ids"]:
        return await ctx.send("You don't have permission to use this command.")

    if not amount.startswith('$'):
        return await ctx.send("Amount must be in $ format, e.g., $5")

    usd = float(amount[1:])
    ltc = usd_to_ltc(usd)
    balances[str(member.id)] = ltc
    await ctx.send(f"Set {member.mention}'s balance to {ltc:.4f} LTC (≈ ${usd:.2f})")

@bot.command()
async def baltop(ctx):
    if not balances:
        return await ctx.send("No balances found.")

    sorted_bal = sorted(balances.items(), key=lambda x: x[1], reverse=True)
    embed = discord.Embed(title="Litecoin Leaderboard", color=0x3498db)

    for i, (uid, amt) in enumerate(sorted_bal[:10]):
        user = await bot.fetch_user(int(uid))
        embed.add_field(name=f"{i+1}. {user.display_name}", value=f"{amt:.4f} LTC", inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="👋 Introduction",
        description=config["messages"]["help_intro"],
        color=0x7289da
    )
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="💰 Wallet", style=discord.ButtonStyle.secondary))
    view.add_item(discord.ui.Button(label="🛠️ Utilities", style=discord.ButtonStyle.secondary))
    view.add_item(discord.ui.Button(label="📜 Terms and conditions", style=discord.ButtonStyle.secondary))
    await ctx.send(embed=embed, view=view)

bot.run(config["token"])
                 
