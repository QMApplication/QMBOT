import random
import discord
from discord.ext import commands

from storage import load_marriages, save_marriages
from ui_utils import C, E, embed, error, warn, success

# target_id -> proposer_id
MARRIAGE_PROPOSALS: dict[str, str] = {}


class ProposalView(discord.ui.View):
    """Shown to the proposal target. They can Accept or Deny."""

    def __init__(self, target: discord.Member, proposer: discord.Member):
        super().__init__(timeout=120)
        self.target   = target
        self.proposer = proposer

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.target.id:
            await interaction.response.send_message(
                embed=error("Marriage", "This proposal isn't for you."), ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Accept 💍", style=discord.ButtonStyle.success)
    async def accept_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        tid, pid = str(self.target.id), str(self.proposer.id)
        marriages = load_marriages()
        MARRIAGE_PROPOSALS.pop(tid, None)
        if marriages.get(pid) or marriages.get(tid):
            await interaction.response.edit_message(
                embed=warn("Marriage", "One of you is already married. 💔"), view=self)
            return
        marriages[pid] = tid
        marriages[tid] = pid
        save_marriages(marriages)
        e = embed(
            "💞  Married!",
            f"{self.target.mention} said **YES** to {self.proposer.mention}!\n\nCongratulations! 🎊",
            C.MARRIAGE,
        )
        await interaction.response.edit_message(embed=e, view=self)
        self.stop()

    @discord.ui.button(label="Deny 💔", style=discord.ButtonStyle.danger)
    async def deny_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        MARRIAGE_PROPOSALS.pop(str(self.target.id), None)
        e = embed(
            "💔  Proposal Rejected",
            f"{self.target.mention} said **no** to {self.proposer.mention}.\n\nOuch.",
            C.LOSE,
        )
        await interaction.response.edit_message(embed=e, view=self)
        self.stop()

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        MARRIAGE_PROPOSALS.pop(str(self.target.id), None)


class Marriage(commands.Cog):
    def __init__(self, bot: commands.Bot):
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
            return await ctx.send(embed=warn("Marriage", "That person already has a pending proposal."))
        MARRIAGE_PROPOSALS[tid] = aid
        view = ProposalView(target=member, proposer=ctx.author)
        e = embed(
            "💍  Proposal!",
            f"{ctx.author.mention} has proposed to {member.mention}!\n\n"
            f"{member.mention}, accept or deny below.",
            C.MARRIAGE,
        )
        await ctx.send(embed=e, view=view)

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
            p_user = await self.bot.fetch_user(int(partner))
            p_name = p_user.mention
        except Exception:
            p_name = f"<@{partner}>"
        e = embed("💔  Divorce", f"{ctx.author.mention} and {p_name} are now divorced.", C.LOSE)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="partner", description="View your or someone else's partner.")
    async def partner(self, ctx, member: discord.Member = None):
        member    = member or ctx.author
        marriages = load_marriages()
        partner   = marriages.get(str(member.id))
        if not partner:
            return await ctx.send(embed=embed("💔  No Partner",
                f"{member.display_name} is not married.", C.NEUTRAL))
        try:
            p_user = await self.bot.fetch_user(int(partner))
            p_name = p_user.display_name
        except Exception:
            p_name = "Unknown"
        e = embed("💗  Partner", f"**{member.display_name}** is married to **{p_name}**. 💍", C.MARRIAGE)
        e.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="flirt", description="Flirt with someone.")
    async def flirt(self, ctx, member: discord.Member):
        if member == ctx.author:
            return await ctx.send(embed=embed("😳  Flirt",
                "Flirting with yourself... confidence, we respect it.", C.MARRIAGE))
        if member.bot:
            return await ctx.send(embed=embed("🤖  Flirt", "Bots don't understand love... yet.", C.NEUTRAL))
        lines = [
            "Are you Wi-Fi? Because I'm feeling a strong connection.",
            "Do you have a map? I keep getting lost in your messages.",
            "If charm were XP, you'd be max level.",
            "You're the reason the server's uptime just improved.",
            "I'd share my last health potion with you. 💖",
        ]
        e = embed("💘  Flirt",
                  f"{ctx.author.mention} → {member.mention}\n\n> {random.choice(lines)}",
                  C.MARRIAGE,
                  footer=f"{ctx.author.display_name} → {member.display_name}")
        await ctx.send(embed=e)


async def setup(bot: commands.Bot):
    await bot.add_cog(Marriage(bot))
