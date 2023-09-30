from .jamcog2 import JamCog2


async def setup(bot):
    await bot.add_cog(JamCog2(bot))