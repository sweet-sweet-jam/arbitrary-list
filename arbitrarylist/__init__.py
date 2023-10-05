from .arbitrarylist import Arbitrarylist


async def setup(bot):
    await bot.add_cog(Arbitrarylist(bot))