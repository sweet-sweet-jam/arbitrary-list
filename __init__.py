from .jamcog1 import JamCog1


async def setup(bot):
    await bot.add_cog(JamCog1(bot))