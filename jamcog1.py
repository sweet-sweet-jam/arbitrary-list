from redbot.core import commands

class JamCog1(commands.Cog):
    """My custom cog"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def mycom(self, ctx):
        """This does stuff!"""
        # Your code will go here
        await ctx.send("I can do stuff!")
 
    @commands.command()
    async def echo(self, ctx, *, message):
        """Echoes the provided message"""
        await ctx.send(message)