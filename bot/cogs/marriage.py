import random
import discord
from discord.ext import commands

from storage import load_marriages, save_marriages
from ui_utils import C, E, embed, error, warn, success

MARRIAGE_PROPOSALS: dict[str, str] = {}


class Marriage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="marry", description="Propose to someone.")
    async def marry(self, ctx, member: discord.Member):
        if member == ctx.author:
            return await ctx.send(embed=error("Marriage", "You can't propose to yourself."))
        if member.bot:
            return await ctx.send(embed=error("Marriage", "Bots don't believe in marriage."))
        marriages = load_marriages()
        aid, tid  = str(ctx.author.id), str(member.id)
        if marriages.get(aid) or marriages.get(tid):
            return await ctx.send(embed=warn("Marriage", "One of you is already married. 💔"))
        if tid in MARRIAGE_PROPOSALS:
            return await ctx.send(embed=warn("Marriage", "That person already has a pending proposal. Wait your turn."))
        MARRIAGE_PROPOSALS[tid] = aid
        e = embed(
            "💍  Proposal Sent!",
            f"{ctx.author.mention} has proposed to {member.mention}!\n\n"
            f"{member.mention}, use `/accept` to say **yes!** 💕",
            C.MARRIAGE,
        )
        await ctx.send(embed=e)

    @commands.hybrid_command(name="accept", description="Accept a marriage proposal.")
    async def accept(self, ctx):
        uid         = str(ctx.author.id)
        proposer_id = MARRIAGE_PROPOSALS.get(uid)
        if not proposer_id:
            return await ctx.send(embed=warn("Marriage", "You have no pending proposals."))
        marriages = load_marriages()
        if marriages.get(proposer_id) or marriages.get(uid):
            MARRIAGE_PROPOSALS.pop(uid, None)
            return await ctx.send(embed=warn("Marriage", "One of you is already married."))
        marriages[proposer_id] = uid
        marriages[uid]         = proposer_id
        save_marriages(marriages)
        MARRIAGE_PROPOSALS.pop(uid, None)
        try:
            proposer = await self.bot.fetch_user(int(proposer_id))
            p_mention = proposer.mention
        except Exception:
            p_mention = f"<@{proposer_id}>"
        e = success("Married! 💞", f"{ctx.author.mention} and {p_mention} are now **married**! 🎊")
        e.color = C.MARRIAGE
        await ctx.send(embed=e)

    @commands.hybrid_command(name="divorce", description="Divorce your partner.")
    async def divorce(self, ctx):
        uid       = str(ctx.author.id)
        marriages = load_marriages()
        partner   = marriages.get(uid)
        if not partner:
            return await ctx.send(embed=warn("Divorce", "You're not married."))
        marriages.pop(uid, None)
        marriages.pop(partner, None)
        save_marriages(marriages)
        try:
            p_user   = await self.bot.fetch_user(int(partner))
            p_name   = p_user.mention
        except Exception:
            p_name   = f"<@{partner}>"
        e = embed("💔  Divorce", f"{ctx.author.mention} and {p_name} are now divorced.", C.LOSE)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="partner", description="View your or someone else's partner.")
    async def partner(self, ctx, member: discord.Member = None):
        member    = member or ctx.author
        marriages = load_marriages()
        partner   = marriages.get(str(member.id))
        if not partner:
            return await ctx.send(embed=embed("💔  No Partner", f"{member.display_name} is not married.", C.NEUTRAL))
        try:
            p_user = await self.bot.fetch_user(int(partner))
            p_name = p_user.display_name
        except Exception:
            p_name = "Unknown User"
        e = embed("💗  Partner", f"**{member.display_name}** is married to **{p_name}**. 💍", C.MARRIAGE)
        e.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="flirt", description="Flirt with someone.")
    async def flirt(self, ctx, member: discord.Member):
        if member == ctx.author:
            return await ctx.send(embed=embed("😳  Flirt", "Flirting with yourself... confidence, we respect it.", C.MARRIAGE))
        if member.bot:
            return await ctx.send(embed=embed("🤖  Flirt", "Bots don't understand love... yet.", C.NEUTRAL))
        lines = [
            "Are you Wi-Fi? Because I'm feeling a strong connection.",
            "Do you have a map? I keep getting lost in your messages.",
            "If charm were XP, you'd be max level.",
            "You're the reason the server's uptime just improved.",
            "I'd share my last health potion with you. 💖",
        ]
        e = embed(
            f"💘  Flirt",
            f"{ctx.author.mention} → {member.mention}\n\n> {random.choice(lines)}",
            C.MARRIAGE,
            footer=f"{ctx.author.display_name} → {member.display_name}",
        )
        await ctx.send(embed=e)


async def setup(bot):
    await bot.add_cog(Marriage(bot))
